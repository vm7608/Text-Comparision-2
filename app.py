import difflib
import json
import re

import streamlit as st


HIGHT_LIGHT_CODE_1 = ":red["
HIGHT_LIGHT_CODE_2 = ":green["
RESET_CODE = "]"


def find_ranges_with_indices(diff_string: str) -> list[tuple[int, int]]:
    """Find ranges with indices that need to be highlighted.

    Args:
        diff_string (str): input diff string get from difflib.Differ().compare

    Returns:
        list[tuple[int, int]]: list of (start_index, end_index) of ranges that need to be highlighted
    """
    patterns = r'(\++|-+|\^+)'
    matches = re.finditer(patterns, diff_string)
    ranges = []
    for match in matches:
        start_index = match.start()
        end_index = match.end() - 1
        ranges.append((start_index, end_index))

    return ranges


def insert_color_tags(
    input_string: str, ranges: list[tuple[int, int]], highlight_code: str
) -> str:
    """Insert color tags to input string at given ranges.

    Args:
        input_string (str): string to be highlighted
        ranges (list[tuple[int, int]]): list of (start_index, end_index) of ranges that need to be highlighted
        highlight_code (str): color code

    Returns:
        str: highlighted string
    """
    offset = 0
    for start, end in ranges:
        modified_start = start + offset
        modified_end = end + offset
        input_string = (
            input_string[:modified_start]
            + highlight_code
            + input_string[modified_start : modified_end + 1]
            + RESET_CODE
            + input_string[modified_end + 1 :]
        )
        offset += len(highlight_code) + len(RESET_CODE)

    return input_string


def highlight_differences(
    diff_result: list[str],
    text1: list[str],
    text2: list[str],
) -> tuple[list[str], list[str]]:
    """Highlight differences between two texts.

    Args:
        diff_result (list[str]): diff result get from difflib.Differ().compare
        text1 (list[str]): list of strings of text1
        text2 (list[str]): list of strings of text2

    Returns:
        tuple[list[str], list[str]]: list of strings of text1 and text2 after highlighted
    """
    result1 = []
    result2 = []
    i1, i2 = 0, 0

    for idx, line in enumerate(diff_result):
        if line.startswith("  "):  # Common line
            result1.append(text1[i1])
            result2.append(text2[i2])
            i1 += 1
            i2 += 1
        elif line.startswith("- "):  # Line removed from text1
            if idx + 1 < len(diff_result) and diff_result[idx + 1].startswith("? "):
                # Line removed from text1 and changed in text2
                diff_ranges = find_ranges_with_indices(diff_result[idx + 1][2:])
                result1.append(
                    insert_color_tags(text1[i1], diff_ranges, HIGHT_LIGHT_CODE_1)
                )
                i1 += 1
            else:
                if idx + 1 < len(diff_result) and diff_result[idx + 1].startswith("- "):
                    # Line removed from text1 and not appear in text2
                    result1.append(HIGHT_LIGHT_CODE_1 + text1[i1] + RESET_CODE)
                    # result2.append("") # TODO: maybe add this line
                if idx + 1 < len(diff_result) and diff_result[idx + 1].startswith("+ "):
                    # Line removed from text1 and appear in text2
                    result1.append(text1[i1])
                    result2.append("")
                i1 += 1

        elif line.startswith("+ "):  # Line added to text2
            if idx + 1 < len(diff_result) and diff_result[idx + 1].startswith("? "):
                # Line from text1 changed in text2
                diff_ranges = find_ranges_with_indices(diff_result[idx + 1][2:])
                result2.append(
                    insert_color_tags(text2[i2], diff_ranges, HIGHT_LIGHT_CODE_2)
                )
                i2 += 1
            else:
                # Line added to text2
                result1.append("")
                result2.append(HIGHT_LIGHT_CODE_2 + text2[i2] + RESET_CODE)
                i2 += 1

    return result1, result2


def read_json(json_path: str):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def main():
    st.set_page_config(layout="wide")
    st.title('Text comparison')
    st.markdown("<hr />", unsafe_allow_html=True)

    if "question_index" not in st.session_state:
        st.session_state["question_index"] = 0

    # Function to update question index
    def update_question_index(new_index):
        st.session_state["question_index"] = new_index

    # Function to update slider
    def update_slider(new_index):
        st.session_state["slider"] = new_index

    # add a next and previous button, if clicked, update question_index and slider
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Previous"):
            update_question_index(max(0, st.session_state["question_index"] - 1))
            update_slider(st.session_state["question_index"] + 1)
    with col2:
        if st.button("Next"):
            update_question_index(
                min(NUMBER_OF_LOGS - 1, st.session_state["question_index"] + 1)
            )
            update_slider(st.session_state["question_index"] + 1)

    # Slider to navigate between questions
    slider_index = st.slider(
        "Select a question",
        min_value=1,
        max_value=NUMBER_OF_LOGS,
        key="slider",
    )
    update_question_index(slider_index - 1)

    # display question
    st.markdown("<hr />", unsafe_allow_html=True)

    question_index = st.session_state["question_index"]
    log_quest = JSON_LOGS[question_index]
    if log_quest:
        st.header(
            f"Question {question_index + 1}/{NUMBER_OF_LOGS} - {log_quest['question_id']}"
        )
        # display question base and improved with highlighted differences
        ground_truth = log_quest["ground_truth"]
        question_base = log_quest["question_base"]

        diff = difflib.Differ().compare(ground_truth, question_base)

        result1, result2 = highlight_differences(
            list(diff), ground_truth, question_base
        )

        # Display in two columns
        col1, col2 = st.columns(2)
        with col1:
            st.header("Ground truth")
            st.markdown(f"**{log_quest['question_id']}**")
            st.markdown("<hr />", unsafe_allow_html=True)
            for line_num, line in enumerate(result1, start=1):
                st.markdown(f":blue[{line_num} &rarr;] {line}", unsafe_allow_html=True)

        with col2:
            st.header("Question base")
            st.markdown(f"**LER: {log_quest['ler_base']}**")
            st.markdown("<hr />", unsafe_allow_html=True)
            for line_num, line in enumerate(result2, start=1):
                st.markdown(f":blue[{line_num} &rarr;] {line}", unsafe_allow_html=True)

        st.markdown("<hr />", unsafe_allow_html=True)
        st.image(log_quest["img_link"], use_column_width=True)


if __name__ == '__main__':
    JSON_LOG_PATH = "visualize_question.json"
    JSON_LOGS = read_json(JSON_LOG_PATH)
    NUMBER_OF_LOGS = len(JSON_LOGS)
    main()
