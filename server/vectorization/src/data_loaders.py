import os
import zipfile

from pathlib import Path
from llama_index import download_loader

from src import config as C

## Get all files and returns a dict based on their extension
def collect_files_by_extension(root_dir):

    """Collect all files under the given root directory, categorized by their extension."""
    # Define the desired file extensions
    desired_extensions = ('.pdf', '.docx', '.pptx', '.xlsx', '.png', '.rtf')
    
    # Initialize a dictionary to hold the results
    files_by_extension = {ext: [] for ext in desired_extensions}
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            _, extension = os.path.splitext(filename)
            # Check if the extension is in our list of desired extensions
            if extension in desired_extensions:
                # Append the full path to the appropriate list in the dictionary
                full_path = os.path.join(dirpath, filename)
                files_by_extension[extension].append(full_path)
                
    # Optionally, remove any extensions that didn't have any files
    files_by_extension = {ext: paths for ext, paths in files_by_extension.items() if paths}
    
    return files_by_extension

def process_pdf(document_path):
    """
    Processes a PDF document, loading its data using a dynamically loaded PDF reader.
    Parameters:
    - document_path (str or Path): The path to the PDF document to be processed.
    Returns:
    - documents: The loaded data from the PDF document.
    """
    try:
        # Ensure the document_path is a Path object
        document_path = Path(document_path)
        
        # Dynamically load the PDF reader
        PDFReader = download_loader("PDFReader")
        if not PDFReader:
            raise ImportError("Failed to load the PDFReader module.")

        loader = PDFReader()
        
        # Load and return the document data
        documents = loader.load_data(file=document_path)
        return documents
    except Exception as e:
        print(f"An error occurred while processing the PDF document: {e}")
        return None

def process_docx(document_path):
    """
    Processes a DOCX document by loading its data using a dynamically loaded DOCX reader.
    Parameters:
    - document_path (str or Path): The path to the DOCX document to be processed.
    Returns:
    - The loaded data from the DOCX document.
    """
    try:
        # Ensure the document_path is a Path object for consistency
        document_path = Path(document_path)
        
        # Dynamically load the DocxReader
        DocxReader = download_loader("DocxReader")
        if not DocxReader:
            raise ImportError("Failed to load the DocxReader module.")
        
        # Initialize the DocxReader and load the document data
        loader = DocxReader()
        documents = loader.load_data(file=document_path)
        return documents
    except Exception as e:
        print(f"An error occurred while processing the DOCX document at {document_path}: {e}")
        return None

def process_pptx(document_path):
    """
    Processes a PPTX document by loading its data using a dynamically loaded PPTX reader.
    Parameters:
    - document_path (str or Path): The path to the PPTX document to be processed.
    Returns:
    - The loaded data from the PPTX document, or None if an error occurs.
    """
    try:
        # Ensure the document_path is a Path object for consistency
        document_path = Path(document_path)
        
        # Dynamically load the PptxReader
        PptxReader = download_loader("PptxReader")
        if not PptxReader:
            raise ImportError("Failed to load the PptxReader module.")
        
        # Initialize the PptxReader and load the document data
        loader = PptxReader()
        documents = loader.load_data(file=document_path)
        return documents
    except zipfile.BadZipFile:
        print(f"The file at {document_path} is not a valid zip file and might be corrupted.")
    except Exception as e:
        print(f"An unexpected error occurred while processing the PPTX document at {document_path}: {e}")

def process_xlsx(document_path):
    """
    Processes an XLSX document by loading its data using a dynamically loaded Pandas Excel reader.
    Parameters:
    - document_path (str or Path): The path to the XLSX document to be processed.
    Returns:
    - The loaded data from the XLSX document, or None if an error occurs.
    """
    try:
        # Ensure the document_path is a Path object for consistency
        document_path = Path(document_path)
        
        # Dynamically load the PandasExcelReader
        PandasExcelReader = download_loader("PandasExcelReader")
        if not PandasExcelReader:
            raise ImportError("Failed to load the PandasExcelReader module.")
        
        # Initialize the PandasExcelReader with specific configuration and load the document data
        loader = PandasExcelReader(pandas_config={"header": 0})
        documents = loader.load_data(file=document_path)
        return documents
    except Exception as e:
        print(f"An error occurred while processing the XLSX document at {document_path}: {e}")
        return None

def process_png(document_path):
    """
    Processes a PNG document by loading its data using a dynamically loaded Image reader.
    If the image contains key-value pairs text, it uses a specific text type for processing.
    Parameters:
    - document_path (str or Path): The path to the PNG document to be processed.
    Returns:
    - The loaded data from the PNG document, or None if an error occurs.
    """
    try:
        # Ensure the document_path is accurately represented as a Path object
        document_path = Path(document_path)
        
        # Dynamically load the ImageReader
        ImageReader = download_loader("ImageReader")
        if not ImageReader:
            raise ImportError("Failed to load the ImageReader module.")
        
        # Initialize the ImageReader with specific configuration and load the document data
        loader = ImageReader(text_type="key_value")
        documents = loader.load_data(file=document_path)  # Use the actual document_path variable
        return documents
    except Exception as e:
        print(f"An error occurred while processing the PNG document at {document_path}: {e}")
        return None
    
def process_rtf(document_path):
    print(f"RTF is not processed at the moment: {document_path}")
    return None

def process_document_by_type(document_path):
    """
    Dispatch function to process a document based on its file extension.
    This function should call the appropriate processing function for each file type.
    """
    _, extension = os.path.splitext(document_path)
    if extension == '.docx':
        return process_docx(document_path)
    if extension == '.pdf':
        return process_pdf(document_path)
    elif extension == '.docx':
        return process_docx(document_path)
    elif extension == '.pptx':
        return process_pptx(document_path)
    elif extension == '.xlsx':
        return process_xlsx(document_path)
    elif extension == '.png':
        return process_png(document_path)
    elif extension == '.rtf':
        return process_rtf(document_path)
    else:
        print(f"No processing function for {extension}")
        return None

def read_documents_from_input(input_dict):
    """
    Process documents from a structured input dictionary,
    where each key is a file extension and each value is a list of paths to files.
    """
    all_documents = []
    for extension, paths in input_dict.items():
        for document_path in paths:
            # print(f">> Processing document: {document_path}")
            processed_document = process_document_by_type(document_path)
            if processed_document is not None:
                all_documents.append(processed_document)
                print(f">>>>> Successfully Processed: {document_path}")

    return all_documents