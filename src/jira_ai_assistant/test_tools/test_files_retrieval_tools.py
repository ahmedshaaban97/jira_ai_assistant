"""
Test script for Files Retrieval tools.
This script tests the PdfFileRetriever tool.

Usage:
    # Run from the project root (jira_ai_assistant/ directory):
    uv run python src/jira_ai_assistant/test_tools/test_files_retrieval_tools.py
    
    # Or run directly:
    uv run python -m jira_ai_assistant.test_tools.test_files_retrieval_tools

Make sure you have:
1. PDF files available for testing in jira_ai_assistant/src/jira_ai_assistant/resume_documents
2. The 'pypdf' or 'PyPDF2' package installed: `pip install pypdf`
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import the tools
# This script is at: jira_ai_assistant/src/jira_ai_assistant/test_tools/test_files_retrieval_tools.py
# We need to add: jira_ai_assistant/src to the path
script_dir = Path(__file__).resolve().parent  # test_tools/
src_dir = script_dir.parent.parent  # src/
sys.path.insert(0, str(src_dir))

from jira_ai_assistant.tools.files_retrieval_tools import PdfFileRetriever

# Path to resume_documents directory
# From project root: src/jira_ai_assistant/resume_documents
RESUME_DOCUMENTS_PATH = src_dir / "jira_ai_assistant" / "resume_documents"


def test_pdf_file_retriever_with_directory():
    """Test retrieving PDFs from a directory."""
    print("\n" + "="*60)
    print("Testing PdfFileRetriever with Directory")
    print("="*60)
    
    tool = PdfFileRetriever()
    
    # Test with resume_documents directory
    test_path = str(RESUME_DOCUMENTS_PATH)
    print(f"\nRetrieving PDFs from: {test_path}")
    
    try:
        pdf_texts = tool._run(path=test_path)
        print(f"\n✓ Successfully loaded {len(pdf_texts)} PDF file(s)")
        
        if pdf_texts:
            print("\nPreview of first document (first 500 characters):")
            print("-" * 60)
            print(pdf_texts[0][:500])
            print("-" * 60)
            if len(pdf_texts) > 1:
                print(f"\n... and {len(pdf_texts) - 1} more PDF(s)")
        else:
            print("\n⚠ No PDF files found in the specified directory")
        
        return True
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("This is expected if no PDF files are found in the directory.")
        return False
    except ImportError as e:
        print(f"\n✗ Error: {e}")
        print("Please install pypdf: pip install pypdf")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


def test_pdf_file_retriever_with_single_file():
    """Test retrieving a single PDF file."""
    print("\n" + "="*60)
    print("Testing PdfFileRetriever with Single File")
    print("="*60)
    
    tool = PdfFileRetriever()
    
    # Try to find a PDF file in the resume_documents directory
    pdf_files = list(RESUME_DOCUMENTS_PATH.glob("*.pdf")) if RESUME_DOCUMENTS_PATH.exists() else []
    
    if not pdf_files:
        print(f"\n⚠ No PDF files found in {RESUME_DOCUMENTS_PATH} to test single file retrieval")
        print("Skipping single file test...")
        return None
    
    test_file = str(pdf_files[0])
    print(f"\nRetrieving PDF from: {test_file}")
    
    try:
        pdf_texts = tool._run(path=test_file)
        print(f"\n✓ Successfully loaded PDF file")
        print(f"Extracted text length: {len(pdf_texts[0])} characters")
        
        print("\nPreview of extracted text (first 500 characters):")
        print("-" * 60)
        print(pdf_texts[0][:500])
        print("-" * 60)
        
        return True
    except ValueError as e:
        print(f"\n✗ Error: {e}")
        return False
    except ImportError as e:
        print(f"\n✗ Error: {e}")
        print("Please install pypdf: pip install pypdf")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


def test_pdf_file_retriever_with_default_path():
    """Test retrieving PDFs with default path (empty string)."""
    print("\n" + "="*60)
    print("Testing PdfFileRetriever with Default Path")
    print("="*60)
    
    tool = PdfFileRetriever()
    
    print("\nRetrieving PDFs with default path (project root)")
    print("Note: This will search the project root, not the resume_documents folder")
    
    try:
        pdf_texts = tool._run(path="")
        print(f"\n✓ Successfully loaded {len(pdf_texts)} PDF file(s) from default path")
        
        if pdf_texts:
            print("\nPreview of first document (first 500 characters):")
            print("-" * 60)
            print(pdf_texts[0][:500])
            print("-" * 60)
        
        return True
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("This is expected if no PDF files are found in the project root.")
        return False
    except ImportError as e:
        print(f"\n✗ Error: {e}")
        print("Please install pypdf: pip install pypdf")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False


def test_pdf_file_retriever_invalid_path():
    """Test error handling with invalid path."""
    print("\n" + "="*60)
    print("Testing PdfFileRetriever with Invalid Path")
    print("="*60)
    
    tool = PdfFileRetriever()
    
    invalid_path = "/nonexistent/path/to/pdfs"
    print(f"\nTesting with invalid path: {invalid_path}")
    
    try:
        pdf_texts = tool._run(path=invalid_path)
        print(f"\n✗ Unexpected success: Should have raised FileNotFoundError")
        return False
    except FileNotFoundError:
        print("\n✓ Correctly raised FileNotFoundError for invalid path")
        return True
    except Exception as e:
        print(f"\n✗ Unexpected error type: {e}")
        return False


def test_pdf_file_retriever_non_pdf_file():
    """Test error handling with non-PDF file."""
    print("\n" + "="*60)
    print("Testing PdfFileRetriever with Non-PDF File")
    print("="*60)
    
    tool = PdfFileRetriever()
    
    # Try to find a non-PDF file in the resume_documents directory or test_tools directory
    test_files = []
    if RESUME_DOCUMENTS_PATH.exists():
        test_files.extend(list(RESUME_DOCUMENTS_PATH.glob("*.txt")))
    # Also check test_tools directory for .py files
    test_files.extend(list(script_dir.glob("*.py")))
    
    if not test_files:
        print("\n⚠ No non-PDF files found to test error handling")
        print("Skipping non-PDF file test...")
        return None
    
    test_file = str(test_files[0])
    print(f"\nTesting with non-PDF file: {test_file}")
    
    try:
        pdf_texts = tool._run(path=test_file)
        print(f"\n✗ Unexpected success: Should have raised ValueError")
        return False
    except ValueError:
        print("\n✓ Correctly raised ValueError for non-PDF file")
        return True
    except Exception as e:
        print(f"\n✗ Unexpected error type: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n" + "="*60)
    print("Checking Dependencies")
    print("="*60)
    
    try:
        import pypdf
        print("\n✓ pypdf is installed")
        return True
    except ImportError:
        try:
            import PyPDF2
            print("\n✓ PyPDF2 is installed")
            return True
        except ImportError:
            print("\n✗ Neither pypdf nor PyPDF2 is installed")
            print("Please install pypdf: pip install pypdf")
            return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Files Retrieval Tools Test Suite")
    print("="*60)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n⚠ Please install required dependencies before running tests.")
        return
    
    results = []
    
    # Test each scenario
    print("\n\nStarting tool tests...")
    
    # Test 1: Directory retrieval
    results.append(("Directory Retrieval", test_pdf_file_retriever_with_directory()))
    
    # Test 2: Single file retrieval
    single_file_result = test_pdf_file_retriever_with_single_file()
    if single_file_result is not None:
        results.append(("Single File Retrieval", single_file_result))
    
    # Test 3: Default path retrieval
    results.append(("Default Path Retrieval", test_pdf_file_retriever_with_default_path()))
    
    # Test 4: Invalid path error handling
    results.append(("Invalid Path Error Handling", test_pdf_file_retriever_invalid_path()))
    
    # Test 5: Non-PDF file error handling
    non_pdf_result = test_pdf_file_retriever_non_pdf_file()
    if non_pdf_result is not None:
        results.append(("Non-PDF File Error Handling", non_pdf_result))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for test_name, passed in results:
        if passed is None:
            status = "⊘ SKIPPED"
        else:
            status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed is True)
    total_tests = sum(1 for _, passed in results if passed is not None)
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")


if __name__ == "__main__":
    main()

