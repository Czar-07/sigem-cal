from pathlib import Path
import re


class CertificateService:

    def __init__(self, base_folder):
        self.base_folder = Path(base_folder)

    def normalize_dc(self, dc):
        """
        Normaliza:
            DC-918
            DC 918
            dc-918
            918

        para:
            DC-918
        """
        if not dc:
            return None

        value = str(dc).strip().upper()

        match = re.search(r"(\d+)", value)

        if not match:
            return None

        return f"DC-{match.group(1)}"

    def find_files(self, dc, year=None):
        """
        Procura todos os arquivos relacionados ao dispositivo.
        """

        normalized = self.normalize_dc(dc)

        if not normalized:
            return []

        if not self.base_folder.exists():
            return []

        search_root = self.base_folder

        if year:
            year_path = self.base_folder / str(year)

            if year_path.exists():
                search_root = year_path

        results = []

        number = normalized.replace("DC-", "")

        for file in search_root.rglob("*"):

            if not file.is_file():
                continue

            filename = file.name.upper()

            # Aceita:
            # DC-918
            # DC_918
            # DC 918

            patterns = [
                f"DC-{number}",
                f"DC_{number}",
                f"DC {number}",
                f"(DC-{number})",
            ]

            if any(pattern in filename for pattern in patterns):

                results.append({
                    "name": file.name,
                    "path": str(file),
                    "extension": file.suffix.lower(),
                    "year": self._detect_year(file),
                    "type": self._detect_type(file),
                })

        return results

    @staticmethod
    def _detect_year(path):
        for part in path.parts:
            if re.fullmatch(r"20\d{2}", part):
                return int(part)

        return None

    @staticmethod
    def _detect_type(path):

        extension = path.suffix.lower()

        if extension == ".pdf":
            return "pdf"

        if extension == ".xlsx":
            return "excel"

        if extension in {".jpg", ".jpeg", ".png"}:
            return "imagem"

        return "outro"