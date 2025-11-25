from pathlib import Path
from typing import List, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# Get absolute path to the resume_documents directory
# __file__ is in: .../jira_ai_assistant/src/jira_ai_assistant/tools/files_retrieval_tools.py
# parent.parent gets us to: .../jira_ai_assistant/src/jira_ai_assistant/
BASE_DIR = Path(__file__).resolve().parent.parent
# Default path for PDF files
DEFAULT_PDF_PATH = (BASE_DIR / "resume_documents").resolve()


class PdfFileRetrieverInput(BaseModel):
    """Input schema for PdfFileRetriever."""
    path: str = Field(
        default="",
        description=f"Directory containing PDFs or a single PDF file path. If empty or not provided, defaults to the resume_documents directory at: {DEFAULT_PDF_PATH}"
    )


class PdfFileRetriever(BaseTool):
    name: str = "pdf_file_retriever"
    description: str = (
        "Read every PDF in the provided path (or a single PDF file) and return their text contents. "
        "Useful for extracting text from PDF documents for analysis or processing. "
        "Returns a list where each item is the extracted text of one PDF, ordered alphabetically by file name."
    )
    args_schema: Type[BaseModel] = PdfFileRetrieverInput

    def _run(self, path: str = "") -> List[str]:
        """
        Read every PDF in the provided path (or a single PDF file) and return their text contents.

        Args:
            path: Directory containing PDFs or a single PDF file. Defaults to jira_ai_assistant/src/jira_ai_assistant/resume_documents if empty.

        Returns:
            List[str]: List where each item is the extracted text of one PDF, ordered alphabetically by file name.

        Raises:
            ImportError: If neither pypdf nor PyPDF2 is installed.
            FileNotFoundError: If the path does not exist or contains no PDFs.
            ValueError: If a provided file is not a PDF.
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            try:
                from PyPDF2 import PdfReader  # type: ignore
            except ImportError as exc:
                raise ImportError(
                    "pdf_file_retriever requires the 'pypdf' or 'PyPDF2' package. "
                    "Install it with `pip install pypdf`."
                ) from exc

        target_path = Path(path).resolve() if path else DEFAULT_PDF_PATH
        if not target_path.exists():
            raise FileNotFoundError(
                f"Provided path does not exist: {target_path}\n"
                f"Current working directory: {Path.cwd()}\n"
                f"Looking for PDFs at: {target_path.absolute()}"
            )

        if target_path.is_file():
            if target_path.suffix.lower() != ".pdf":
                raise ValueError(f"Expected a PDF file but got: {target_path}")
            pdf_files = [target_path]
        else:
            pdf_files = sorted(
                file for file in target_path.iterdir() if file.is_file() and file.suffix.lower() == ".pdf"
            )
            if not pdf_files:
                raise FileNotFoundError(f"No PDF files found in: {target_path}")

        documents: List[str] = []
        for pdf_file in pdf_files:
            reader = PdfReader(str(pdf_file))
            pages = [page.extract_text() or "" for page in reader.pages]
            documents.append("\n".join(pages).strip())

        return documents
