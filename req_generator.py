import subprocess
import sys
from importlib.metadata import distributions, version
import re


def generate_requirements():
    # Získání seznamu všech nainstalovaných balíčků
    installed_packages = [dist.metadata['Name'] for dist in distributions()]

    requirements = []

    for package in installed_packages:
        try:
            # Získání verze balíčku
            package_version = version(package)

            # Vyloučení standardních knihoven a lokálních balíčků
            if not package.startswith('_') and not re.match(r'^[a-zA-Z]:\\', package):
                requirements.append(f"{package}=={package_version}")
        except Exception as e:
            print(f"Chyba při zpracování balíčku {package}: {str(e)}")

    # Zápis do souboru requirements.txt
    with open('requirements.txt', 'w') as f:
        for item in sorted(requirements):
            f.write(f"{item}\n")

    print("requirements.txt byl úspěšně vygenerován.")

# Spuštění funkcí
if __name__ == "__main__":
    print("Generování requirements.txt pomocí importlib.metadata:")
    generate_requirements()