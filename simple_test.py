content = """Line 1 of test.
Line 2 with "quotes" and 'apostrophes'.
Line 3 has a tab:	 and a newline character here.
Line 4 after explicit newline.
"""

with open(r"c:\kortana\multi_line_test_out.txt", "w") as f:
    f.write(content)

print("Successfully wrote multi-line test to c:/kortana/multi_line_test_out.txt")
