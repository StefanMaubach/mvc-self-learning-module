import os, json, re, argparse

# ============================== CONSTANTS ==============================

REGEX = {
    "document": r"(?s)\\begin{document}(.*)\\end{document}",
    "exercise": r"\\section{(.*)}",
    "hint": r"\\subsection{(.*)}",
    "enumerate": r"\\begin{enumerate}(.*)\\end{enumerate}",
    "itemize": r"\\begin{itemize}(.*)\\end{itemize}",
    "figure": r"\\begin{figure}(.*)\\end{figure}",
    "image": r"\\includegraphics.*?{(.*)}",
    # Detect up to 3 levels nested {}
    "emph": r"(?s)\\emph{((?:[^{}]*|{(?:[^{}]*|{[^{}]*})*})*)}",
    "italics": r"(?s)\\textit{((?:[^{}]*|{(?:[^{}]*|{[^{}]*})*})*)}",
    "bold": r"(?s)\\textbf{((?:[^{}]*|{(?:[^{}]*|{[^{}]*})*})*)}",
    "underlined": r"(?s)\\underline{((?:[^{}]*|{(?:[^{}]*|{[^{}]*})*})*)}",
}

IMAGE_ENVS_HTML = {
    "Question": lambda img_path: '<span class="image object">\n'
    + f'<img src="{img_path}" alt="" />\n'
    + "</span>\n",
    "Hint": lambda img_path: '<div class="image center">\n<span class="image object">\n'
    + f'<img src="{img_path}" width="600" alt="" />\n'
    + "</span>\n</div>\n",
}

REMOVE_FROM_TEX = ("\\clearpage", "\\newpage")

# Load paths
with open("paths.json", "r") as f:
    PATHS = json.load(f)


# ============================== PARSE LATEX ==============================


def clean_tex(raw_tex: str) -> str:
    for term in REMOVE_FROM_TEX:
        raw_tex = raw_tex.replace(term, "")
    return raw_tex


def split_with_names(text: str, regex: str) -> tuple[list, list]:
    split = re.split(regex.replace("(", "").replace(")", ""), text)
    split_names = re.findall(regex, text)

    return split_names, split


def parse_content(content: str) -> list[tuple[str, str]]:
    # Combined pattern to detect all elements
    combined_pattern = (
        f"({REGEX['enumerate']})|({REGEX['itemize']})|({REGEX['figure']})"
    )

    # Find all matches for each pattern, and store the type along with the match
    elements = []
    last_end = 0

    for match in re.finditer(combined_pattern, content, flags=re.DOTALL):
        start = match.start()
        end = match.end()

        # Extract pure text before the current match
        if start > last_end:
            pure_text = content[last_end:start].strip()
            if pure_text:
                elements.append(("text", pure_text))

        # Determine the type of the current match
        if match.group(2):  # enumerate match
            elements.append(("enumerate", match.group(2).strip()))
        elif match.group(4):  # itemize match
            elements.append(("itemize", match.group(4).strip()))
        elif match.group(6):  # figure match
            elements.append(("figure", match.group(6).strip()))

        last_end = end

    # Add any remaining pure text after the last detected element
    if last_end < len(content):
        pure_text = content[last_end:].strip()
        if pure_text:
            elements.append(("text", pure_text))

    return elements


def parse_tex_file(file_path: str) -> dict[str, list[tuple[str, str]]]:
    # Read raw tex
    with open(file_path, "r") as f:
        raw_tex = clean_tex(f.read())

    # Extract the document content (no preamble)
    document = re.search(REGEX["document"], raw_tex).group(1)

    # Split exercises with their names
    exercise_names, exercise_list = split_with_names(document, REGEX["exercise"])
    exercise_list = exercise_list[1:]  # Remove header

    # Parse each exercise
    Exercises = {}
    for ex_name, ex_text in zip(exercise_names, exercise_list):
        # Get question and hints along with their names
        hint_names, question_and_hints = split_with_names(ex_text, REGEX["hint"])

        assert len(question_and_hints) > 1, (
            "Make sure that the exercise contains at least a question and a hint. "
            + "Make sure that each hint is labelled by \\subsection{HINT NAME}"
        )

        # Parse question and hints and store them in a dict structure
        Exercises[ex_name] = {
            "Question": parse_content(question_and_hints[0]),
            "Hints": [
                (hint_name, parse_content(hint))
                for hint_name, hint in zip(hint_names, question_and_hints[1:])
            ],
        }

    return Exercises


# ============================== MAKE AND SAVE HTML EXERCISE ==============================


def make_img_path(figure_content: str) -> str:
    img_path = re.findall(REGEX["image"], figure_content)[0]
    if not os.path.exists(img_path):
        temp_path = os.path.join(PATHS["IMAGES_PATH"], img_path)
        if os.path.exists(temp_path):
            img_path = temp_path
        else:
            raise FileNotFoundError(
                f"The image {img_path} path is not found by itself or in {PATHS['IMAGES_PATH']}."
            )

    return os.path.normpath(img_path)


def make_content(elements: list[tuple[str, str]], mode: str) -> tuple[str, list]:
    content = ""
    leftovers = []
    for element_type, element_content in elements:

        # Text
        if element_type == "text":
            # Line break
            element_content = element_content.replace("\n\n", "\n<br><br>\n")

            if mode == "Question":
                content += f"{element_content}\n"
            elif mode == "Hint":
                content += f"<p>\n{element_content}\n</p>\n"

        # Enumerate
        elif element_type == "enumerate":
            content += (
                "<ol>\n<li>"
                + "</li>\n<li>".join(element_content.split("\\item")[1:])
                + "</li>\n</ol>\n"
            )

        # Itemize
        elif element_type == "itemize":
            content += (
                "<ul>\n<li>"
                + "</li>\n<li>".join(element_content.split("\\item")[1:])
                + "</li>\n</ul>\n"
            )

        # Figure
        elif element_type == "figure":
            if mode == "Question":
                leftovers.append((element_type, element_content))
            elif mode == "Hint":
                img_path = make_img_path(element_content)
                content += IMAGE_ENVS_HTML["Hint"](img_path)

        else:
            leftovers.append((element_type, element_content))

    return content, leftovers


def make_html_exercise(
    exercise_name: str, exercise_content: dict, ex_template: str, hint_template: str
) -> str:

    # QUESTION

    question_content, leftovers = make_content(exercise_content["Question"], "Question")

    exercise_html = ex_template.replace(
        "<!-- EXERCISE NUMBER HERE -->",
        exercise_name,
    ).replace(
        "<!-- WRITE EXERCISE HERE -->",
        "<!-- WRITE EXERCISE HERE -->\n" + question_content,
    )

    # Add one figure
    for element_type, element_content in leftovers:
        if element_type == "figure":
            img_path = make_img_path(element_content)
            exercise_html = exercise_html.replace(
                "<!-- UNCOMMENT TO ADD PICTURE HERE -->",
                "<!-- UNCOMMENT TO ADD PICTURE HERE -->\n"
                + IMAGE_ENVS_HTML["Question"](img_path),
            )
        break

    # HINTS

    hints_html_list = []
    for i, (hint_name, hint_elements) in enumerate(exercise_content["Hints"]):
        # Button name
        hint_html = hint_template.replace("$", str(i + 1)).replace(
            "<!-- WRITE HINT TYPE HERE -->",
            hint_name,
        )

        # Add hint elements in sequence
        hint_content, _ = make_content(hint_elements, "Hint")
        # Make hint and save it in a list
        hint_html = hint_html.replace(
            "<!-- WRITE HINT HERE -->", "<!-- WRITE HINT HERE -->\n" + hint_content
        )
        hints_html_list.append(hint_html)

    # Append all hints
    exercise_html = exercise_html.replace(
        "<!-- ADD HINTS HERE -->",
        "<!-- ADD HINTS HERE -->\n\n" + "\n\n".join(hints_html_list),
    )

    # Convert \emph{text} to <em>text</em>
    exercise_html = re.sub(REGEX["emph"], r"<em>\1</em>", exercise_html)

    # Convert \textit{text} to <i>text</i>
    exercise_html = re.sub(REGEX["italics"], r"<i>\1</i>", exercise_html)

    # Convert \textbf{text} to <b>text</b>
    exercise_html = re.sub(REGEX["bold"], r"<b>\1</b>", exercise_html)

    # Convert \underline{text} to <u>text</u>
    exercise_html = re.sub(REGEX["underlined"], r"<u>\1</u>", exercise_html)

    return exercise_html


def load_templates(templates_path: str) -> tuple[str, str]:
    # Template for entire exercise
    with open(
        os.path.join(templates_path, PATHS["TEMPLATE_NAMES"]["exercise"]), "r"
    ) as f:
        ex_template = f.read()

    # Template for hint
    with open(os.path.join(templates_path, PATHS["TEMPLATE_NAMES"]["hint"]), "r") as f:
        hint_template = f.read()

    return ex_template, hint_template


def save_exercise_to_html(exercise_html: str, exercise_path: str = "test.html") -> None:
    with open(exercise_path, "w") as f:
        f.write(exercise_html)


def update_sidebar(exercise_path: str, exercise_name: str) -> None:
    with open(PATHS["SIDEBAR_PATH"], "r") as f:
        sidebar_text = f.read()

    ex_link = f'<li><a href="{exercise_path}">{exercise_name}</a></li>'

    if ex_link not in sidebar_text:
        sidebar_text = sidebar_text.replace("</ul>", f"{ex_link}\n</ul>")
        with open(PATHS["SIDEBAR_PATH"], "w") as f:
            f.write(sidebar_text)


# ============================== ARG_PARSER ==============================


def make_args() -> tuple[list | str, str]:
    parser = argparse.ArgumentParser(
        description="Convert a latex document to an HTML file."
    )
    parser.add_argument(
        "exercises",
        type=str,
        help=(
            "The number(s) of the exercise(s) you want to convert, starting from 1. "
            + "Can be: an integer (e.g. 1), "
            + "a list of integers separated by comma (with no spaces) (e.g. 1,2,3), "
            + "or the word 'all' (without '') if you want to convert all the exercises in the document."
        ),
    )
    parser.add_argument(
        "--tex_path", type=str, default=PATHS["FILE_PATH"], help="Path to the tex file."
    )
    args = parser.parse_args()

    try:
        exs_num = [int(args.exercises)]
    except ValueError:
        try:
            exs_num = [int(ex) for ex in args.exercises.split(",")]
        except ValueError:
            assert args.exercises == "all", (
                "The input must be an integer (e.g. 1), "
                + "a list of integers separated by comma (with no spaces) (e.g. 1,2,3), "
                + "or the word 'all' (without '') if you want to convert all the exercises in the document."
            )
            exs_num = args.exercises

    return exs_num, args.tex_path


# ============================== RUN ==============================

if __name__ == "__main__":
    exs_num, tex_path = make_args()
    ex_template, hint_template = load_templates(PATHS["TEMPLATES_PATH"])
    Exercises = parse_tex_file(tex_path)

    if exs_num == "all":
        exs_num = list(range(1, len(Exercises) + 1))

    print(f"Source: '{tex_path}'")
    for i, (ex_name, ex_content) in enumerate(Exercises.items()):
        if (i + 1) in exs_num:
            try:
                ex = make_html_exercise(ex_name, ex_content, ex_template, hint_template)
                save_exercise_to_html(ex, exercise_path=f"ex_{i+1}.html")
                update_sidebar(f"ex_{i+1}.html", ex_name)
                print(
                    f" - '{ex_name}' successfully converted to 'ex_{i+1}.html' and added to sidebar."
                )
                exs_num.remove(i + 1)
            except Exception as e:
                print(
                    f" ! '{ex_name}' was not converted because of the following exception:"
                )
                print(e)

    for i in exs_num:
        print(f" ! 'Exercise {i}' was not found in '{tex_path}'")
