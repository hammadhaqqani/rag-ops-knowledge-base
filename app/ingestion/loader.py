"""Document loader for various file formats."""

import logging
from pathlib import Path
from typing import Dict, Optional

import pypdf

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Loads documents from various file formats."""

    SUPPORTED_EXTENSIONS = {".md", ".markdown", ".txt", ".pdf"}

    async def load(self, file_path: str) -> Optional[Dict[str, str]]:
        """
        Load a document from a file path.

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary with 'content' and 'name' keys, or None if loading fails
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return None

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            logger.error(f"Unsupported file type: {path.suffix}")
            return None

        try:
            if path.suffix.lower() == ".pdf":
                content = await self._load_pdf(path)
            elif path.suffix.lower() in {".md", ".markdown"}:
                content = await self._load_markdown(path)
            else:  # .txt
                content = await self._load_text(path)

            if content:
                return {
                    "content": content,
                    "name": path.name,
                    "path": str(path),
                }
            return None

        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}", exc_info=True)
            return None

    async def _load_pdf(self, path: Path) -> Optional[str]:
        """Load content from a PDF file."""
        try:
            with open(path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)
                text_parts = []

                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

                return "\n\n".join(text_parts) if text_parts else None

        except Exception as e:
            logger.error(f"Error loading PDF {path}: {e}", exc_info=True)
            return None

    async def _load_markdown(self, path: Path) -> Optional[str]:
        """Load content from a Markdown file."""
        try:
            with open(path, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error loading Markdown {path}: {e}", exc_info=True)
            return None

    async def _load_text(self, path: Path) -> Optional[str]:
        """Load content from a text file."""
        try:
            with open(path, "r", encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error loading text file {path}: {e}", exc_info=True)
            return None

    async def load_directory(self, directory_path: str) -> list[Dict[str, str]]:
        """
        Load all supported documents from a directory.

        Args:
            directory_path: Path to the directory

        Returns:
            List of loaded documents
        """
        path = Path(directory_path)

        if not path.is_dir():
            logger.error(f"Not a directory: {directory_path}")
            return []

        documents = []
        for file_path in path.rglob("*"):
            if (
                file_path.is_file()
                and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS
            ):
                doc = await self.load(str(file_path))
                if doc:
                    documents.append(doc)

        logger.info(f"Loaded {len(documents)} documents from {directory_path}")
        return documents
