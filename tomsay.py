#! /usr/bin/python
import sys

tom = """              \       _____
               \     /     \\
                \   | (o|o) |
                 \  |   _\  |
                    | '---' |
                     \_____/
           _\___    ___| |____
             |_/\  /   '-'    \    @ @@ @
               \ \|  .GOOGLE.  |     @@@
                \   /       |  |   @
                 \ /|       |  |   @@
                    |_______|_/  @
                    |       |_\/
                    |  .-.  |
                    |  | |  |
                    '._| |_.'
                    /__| |__\\
"""

MSG_WIDTH = 40

def split_lines(words):
    full_lines = len(words)/MSG_WIDTH
    line = 0
    msg_list = ['']
    for word in words:
        line_len = len(msg_list[line])
        if line_len > MSG_WIDTH:
            msg_list.append('')
            line = line + 1
        msg_list[line] = ' '.join((msg_list[line], word)).strip()
    return msg_list

def add_spaces(length, string):
    return string + (' ' * (length - len(string)))

def build_bubble(msg):
    lines = split_lines(msg)
    longest_line = 0
    for line in lines:
        if len(line) > longest_line:
            longest_line = len(line)
    s = [' ' + ('_'*longest_line) + '_' + ' ']
    for line in lines:
        if line == lines[0]:
            s.append("/ " + add_spaces(longest_line, line) + " \\")
        elif line == lines[-1]:
            s.append("\\ " + add_spaces(longest_line, line) + " /")
        else:
            s.append("| " + add_spaces(longest_line, line) + " |")
    s.append(' ' + ('-'*longest_line) + '-' + ' ')
    return '\n'.join(s)


def main():
    msg = sys.argv[1:]
    bubble = build_bubble(msg)
    print bubble + '\n' + tom + '\n'

if __name__ == "__main__":
    main()
