package xstrings

import (
	"testing"
	"unicode/utf8"
)

// criterionSqueeze uses range offsets and a direct predicate rather than the
// candidate's output state machine or its pattern translator.
func criterionSqueeze(input string, selected func(rune) bool) string {
	type segment struct {
		start int
		r     rune
	}
	segments := make([]segment, 0, len(input)+1)
	for start, r := range input {
		segments = append(segments, segment{start, r})
	}
	segments = append(segments, segment{len(input), 0})
	output := make([]byte, 0, len(input))
	for i := 0; i+1 < len(segments); i++ {
		current := segments[i]
		if i > 0 && current.r == segments[i-1].r && selected(current.r) {
			continue
		}
		output = append(output, input[current.start:segments[i+1].start]...)
	}
	return string(output)
}

func TestCriterionSqueezeBytePreservation(t *testing.T) {
	patterns := []struct {
		pattern  string
		selected func(rune) bool
	}{
		{"", func(r rune) bool { return true }},
		{"a", func(r rune) bool { return r == 'a' }},
		{"ab", func(r rune) bool { return r == 'a' || r == 'b' }},
		{"z", func(r rune) bool { return r == 'z' }},
		{"^a", func(r rune) bool { return r != 'a' }},
		{"^", func(r rune) bool { return true }},
		{"a-c", func(r rune) bool { return r >= 'a' && r <= 'c' }},
		{"c-a", func(r rune) bool { return r >= 'a' && r <= 'c' }},
		{"\x00", func(r rune) bool { return r == 0 }},
		{"\ufffd", func(r rune) bool { return r == utf8.RuneError }},
		{"\xff", func(r rune) bool { return r == utf8.RuneError }},
		{"^\ufffd", func(r rune) bool { return r != utf8.RuneError }},
		{"中", func(r rune) bool { return r == '中' }},
		{"中-文", func(r rune) bool { return r >= '中' && r <= '文' }},
		{`\-\^\\`, func(r rune) bool { return r == '-' || r == '^' || r == '\\' }},
	}
	checks := 0
	check := func(input string) {
		for _, pattern := range patterns {
			want := criterionSqueeze(input, pattern.selected)
			if got := Squeeze(input, pattern.pattern); got != want {
				t.Fatalf("Squeeze(%q, %q) = %q, want %q", input, pattern.pattern, got, want)
			}
			checks++
		}
	}

	// Every possible one- and two-byte input, including all isolated continuation
	// bytes, leading bytes, ASCII bytes, NUL, and valid two-byte sequences.
	check("")
	for a := 0; a < 256; a++ {
		check(string([]byte{byte(a)}))
		for b := 0; b < 256; b++ {
			check(string([]byte{byte(a), byte(b)}))
		}
	}

	// Up to four tokens cover output initialization, alternating selected and
	// unselected repeats, real U+FFFD next to invalid bytes, truncated sequences,
	// invalid surrogate encodings, and code points beyond Unicode's limit.
	tokens := []string{"a", "b", "\x00", "\xff", "\xfe", "\ufffd", "中", "文", "\xc2", "\x80", "\xed\xa0\x80", "\xf4\x90\x80\x80", "-", "^", "\\"}
	var visit func(string, int)
	visit = func(input string, depth int) {
		if depth == 0 {
			return
		}
		for _, token := range tokens {
			next := input + token
			check(next)
			visit(next, depth-1)
		}
	}
	visit("", 4)
	t.Logf("checked %d input/pattern pairs against a byte-span oracle", checks)
}
