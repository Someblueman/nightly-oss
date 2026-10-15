// Independent checker derived from claim.md before reading candidate code/tests.
package xstrings_test

import (
	"testing"
	"unicode/utf8"

	"github.com/huandu/xstrings"
)

func TestIndependentSqueezeExamples(t *testing.T) {
	cases := []struct {
		name, input, pattern, want string
	}{
		{"selected_before_invalid", "aa\xff", "a", "a\xff"},
		{"no_selected_runes", "aa\xff\xfe", "z", "aa\xff\xfe"},
		{"unselected_duplicates", "bb\xff\xff", "a", "bb\xff\xff"},
		{"invalid_before_selected", "\xffaa", "a", "\xffa"},
		{"invalid_between_selected", "aa\xffaa", "a", "a\xffa"},
		{"invalid_run_selected", "\xff\xfe\x80", "\ufffd", "\xff"},
		{"literal_replacement_first", "\ufffd\xff\xfe", "\ufffd", "\ufffd"},
		{"invalid_replacement_first", "\xff\ufffd\xfe", "\ufffd", "\xff"},
		{"unicode_with_invalid_tail", "éé\xe2\x82", "é", "é\xe2\x82"},
		{"nul_selected", "\x00\x00\xff", "\x00", "\x00\xff"},
		{"empty_input", "", "a", ""},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			if got := xstrings.Squeeze(tc.input, tc.pattern); got != tc.want {
				t.Errorf("Squeeze(% x, %q) = % x; want % x", []byte(tc.input), tc.pattern, []byte(got), []byte(tc.want))
			}
		})
	}
}

// This oracle supports only a literal single-rune selector. It compares decoded
// adjacent runes, but appends retained input byte slices rather than encoding runes.
func independentLiteralSqueeze(input string, selected rune) string {
	output := make([]byte, 0, len(input))
	var previous rune
	havePrevious := false
	for offset := 0; offset < len(input); {
		r, width := utf8.DecodeRuneInString(input[offset:])
		if !havePrevious || r != previous || r != selected {
			output = append(output, input[offset:offset+width]...)
		}
		previous, havePrevious = r, true
		offset += width
	}
	return string(output)
}

func TestIndependentSqueezeLiteralOracle(t *testing.T) {
	alphabet := []byte{0, 'a', 'b', 0x80, 0x82, 0xa9, 0xac, 0xc3, 0xe2, 0xef, 0xbf, 0xbd, 0xff}
	selectors := []rune{'a', 'b', 'z', 0, 'é', utf8.RuneError}
	checked, mismatches := 0, 0
	var walk func([]byte, int)
	walk = func(input []byte, remaining int) {
		for _, selected := range selectors {
			want := independentLiteralSqueeze(string(input), selected)
			got := xstrings.Squeeze(string(input), string(selected))
			checked++
			if got != want {
				mismatches++
				if mismatches <= 12 {
					t.Errorf("input=% x selected=%U got=% x want=% x", input, selected, []byte(got), []byte(want))
				}
			}
		}
		if remaining > 0 {
			for _, b := range alphabet {
				walk(append(input, b), remaining-1)
			}
		}
	}
	walk(nil, 4)
	t.Logf("checked=%d mismatches=%d", checked, mismatches)
}
