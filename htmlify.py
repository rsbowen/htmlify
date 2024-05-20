"""
   A tool for taking a collection of outputs and putting them into a single HTML file for easy viewing and sharing.
   All the data is encoded in the file (in base64) so that it can be shared directly.

   Typical usage is to use shell globbing to select the files you want to include, e.g.

   python htmlify.py out.html debug_outputs/*.png
   """

import base64
import datetime

from abc import abstractclassmethod
from pathlib import Path
from typing import List

import typer

from autoregistry import Registry


class Handler(Registry, suffix="Handler"):
    """Class that handles a single file type"""

    @classmethod
    def header(cls) -> str:
        """If this file type requires a header, return it here."""
        return ""

    @abstractclassmethod
    def htmlify(cls, filename: str) -> str:
        """Convert a file on disk to HTML that will sensibly display the file."""
        pass


class ImageHandler(Handler, aliases=["jpg", "jpeg", "png", "gif"]):
    """Class that handles images"""

    @classmethod
    def htmlify(cls, path: Path) -> str:
        extension = path.suffix.replace(".", "").lower()
        with open(path, "rb") as f:
            return f"<img src = 'data:image/{extension};base64,{base64.b64encode(f.read()).decode()}'/>"


class GLBHandler(Handler, aliases=["glb", "gltf"]):
    """Class that handles GLB"""

    @classmethod
    def header(cls) -> str:
        script_import = """
            <script type='module' src='https://ajax.googleapis.com/ajax/libs/model-viewer/3.3.0/model-viewer.min.js'>
            </script>
        """
        style = """<style>
                   model-viewer {
                     width: 512px;
                     height: 512px;
                   }
                   </style>"""
        return script_import + "\n" + style

    @classmethod
    def htmlify(cls, path: Path) -> str:
        extension = path.suffix.replace(".", "").lower()
        format = "gltf-binary" if extension == "glb" else "gltf-text"
        with open(path, "rb") as f:
            return f"""
                <model-viewer camera-controls src='data:model/{format};base64,{base64.b64encode(f.read()).decode()}'>
                </model-viewer>"""


def main(outfile: Path, files: List[Path]):
    headers = {}
    body = []
    for f in files:
        extension = f.suffix.replace(".", "").lower()
        if extension not in Handler:
            print(f"No handler for {f} with extension {extension}")
            continue
        handler = Handler[extension]
        handler_name = handler.__registry__.name
        if handler_name not in headers:
            headers[handler_name] = handler.header()
        body.append(f"<h1> {f} </h1>")
        body.append(handler.htmlify(f))
        body.append("<hr>")

    with open(outfile, "w") as f:
        f.write("<html><head>")
        for header in headers.values():
            f.write(header)
        f.write("</head><body>")
        for line in body:
            f.write(line + "\n")
        f.write("<hr>")
        f.write(f"Generated at {datetime.datetime.now()}")
        f.write("</body></html>")


if __name__ == "__main__":
    typer.run(main)

