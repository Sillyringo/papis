"""
This module controls the notes for every papis document.
"""
import os

import papis.config
import papis.api
import papis.format
import papis.document
import papis.utils
import papis.hooks
import papis.logging

logger = papis.logging.get_logger(__name__)


def has_notes(doc: papis.document.Document) -> bool:
    """Checks if the document has notes."""
    return "notes" in doc


def notes_path(doc: papis.document.Document) -> str:
    """Get the path to the notes file corresponding to *doc*.

    If the document does not have attached notes, a filename is constructed (using
    the :ref:`config-settings-notes-name` setting) in the document's main folder.

    :returns: a absolute filename that corresponds to the attached notes for
        *doc* (this file does not neccessarily exist).
    """
    if not has_notes(doc):
        notes_name = papis.format.format(papis.config.getstring("notes-name"), doc,
                                         default="notes.tex")
        doc["notes"] = papis.utils.clean_document_name(notes_name)
        papis.api.save_doc(doc)

    return os.path.join(doc.get_main_folder() or "", doc["notes"])


def notes_path_ensured(doc: papis.document.Document, notext: bool) -> str:
    """Get the path to the notes file corresponding to *doc* or create it if
    it does not exist.

    If the notes do not exist, a new file is created using :func:`notes_path`
    and filled with the contents of the template given by the
    :ref:`config-settings-notes-template` configuration option.

    :returns: an absolute filename that corresponds to the attached notes for *doc*.
    """
    notespath = notes_path(doc)

    if not os.path.exists(notespath):
        templatepath = os.path.expanduser(papis.config.getstring("notes-template"))

        template = ""
        if os.path.exists(templatepath):
            with open(templatepath, encoding="utf-8") as fd:
                try:
                    template = papis.format.format(fd.read(), doc)
                except papis.format.FormatFailedError as exc:
                    logger.error("Failed to format notes template at '%s'.",
                                 templatepath, exc_info=exc)
        
        if (not notext):
            import re
            from pdfminer.high_level import extract_text
                
            for file in doc.get_files():
                pdf_text = extract_text(file)
                
                for mobj in list(reversed(list(re.finditer('[^\s] *\n *[^\s]', pdf_text)))):
                    pdf_text = pdf_text[:mobj.start() + 1] + ' ' + pdf_text[mobj.end() - 1:]

                template += pdf_text
        
        with open(notespath, "w+", encoding="utf-8") as fd:
            fd.write(template)

    return notespath