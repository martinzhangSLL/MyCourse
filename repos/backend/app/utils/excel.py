from io import BytesIO
from openpyxl import load_workbook


def read_student_import(file_content: bytes) -> list[tuple[str, str]]:
    """
    Read student import Excel file.

    Args:
        file_content: The Excel file content as bytes.

    Returns:
        List of tuples containing (name, student_no).

    Raises:
        ValueError: If the Excel file format is invalid.
    """
    try:
        workbook = load_workbook(BytesIO(file_content))
        sheet = workbook.active

        students: list[tuple[str, str]] = []

        # Skip header row if present, start from row 2
        for row in sheet.iter_rows(min_row=2, max_col=2, values_only=True):
            name, student_no = row
            if name is not None and student_no is not None:
                students.append((str(name).strip(), str(student_no).strip()))

        return students
    except Exception as e:
        raise ValueError(f"Failed to read Excel file: {e}")
