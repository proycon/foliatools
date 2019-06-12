FoLiA Tools
=================

A number of command-line tools are readily available for working with FoLiA, to various ends. The following tools are currently available:

- ``foliavalidator`` -- Tests if documents are valid FoLiA XML. **Always use this to test your documents if you produce your own FoLiA documents!**
- ``foliaquery`` -- Advanced query tool that searches FoLiA documents for a specified pattern, or modifies a document according to the query. Supports FQL (FoLiA Query Language) and CQL (Corpus Query Language).
- ``foliaeval`` -- Evaluation tool, can compute various evaluation metrics for selected annotation types, either against
  a gold standard reference or as a measure of inter-annotated agreement.
- ``folia2txt`` -- Convert FoLiA XML to plain text (pure text, without any annotations)
- ``folia2annotatedtxt`` -- Like above, but produces output simple
  token annotations inline, by appending them directly to the word using a specific delimiter.
- ``folia2columns`` -- This conversion tool reads a FoLiA XML document
  and produces a simple columned output format (including CSV) in which each token appears on one line. Note that only simple token annotations are supported and a lot of FoLiA data can not be intuitively expressed in a simple columned format!
- ``folia2html`` -- Converts a FoLiA document to a semi-interactive HTML document, with limited support for certain token annotations.
- ``folia2dcoi`` -- Convert FoLiA XML to D-Coi XML (only for annotations supported by D-Coi)
- ``foliatree`` -- Outputs the hierarchy of a FoLiA document.
- ``foliacat`` -- Concatenate multiple FoLiA documents.
- ``foliacount`` -- This script reads a FoLiA XML document and counts certain structure elements.
- ``foliacorrect`` -- A tool to deal with corrections in FoLiA, can automatically accept suggestions or strip all corrections so parsers that don't know how to handle corrections can process it.
- ``foliaerase`` -- Erases one or more specified annotation types from the FoLiA document.
- ``folialangid`` -- Does language recognition on FoLiA documents, assigns language identifiers to different substructures
- ``foliaid`` -- Assigns IDs to elements in FoLiA documents
- ``foliafreqlist`` -- Output a frequency list on tokenised FoLiA documents.
- ``foliamerge`` -- Merges annotations from two or more FoLiA documents.
- ``foliatextcontent`` -- A tool for adding or stripping text redundancy, supports adding offset information.
- ``foliaupgrade`` -- Upgrades a document to the latest FoLiA version.
- ``alpino2folia`` -- Convert Alpino-DS XML to FoLiA XML
- ``dcoi2folia`` -- Convert D-Coi XML to FoLiA XML
- ``conllu2folia`` -- Convert files in the `CONLL-U format <http://http://universaldependencies.org/format.html>`_ to FoLiA XML.
- ``rst2folia`` -- Convert ReStructuredText, a lightweight non-intrusive text markup language, to FoLiA, using `docutils <http://docutils.sourceforge.net/>`_.
- ``tei2folia`` -- Convert a subset of TEI to FoLiA.

All of these tools are written in Python, and thus require a Python (2.7, 3 or higher) installation to run. More tools are added as time progresses.

Installation
---------------

The FoLiA tools are published to the Python Package Index and can be installed effortlessly using ``pip``, from the command-line, type::

  $ pip install folia-tools

You may need to use ``pip3`` to ensure you have the Python 3 version.  Add ``sudo`` to install it globally on your system, but we strongly
recommend you use virtualenv to make a self-contained Python environment.

The FoLiA tools are also included in our `LaMachine distribution <https://proycon.github.io/lamachine>`_ .


Installation Troubleshooting
-------------------------------

If ``pip`` is not yet available, install it as follows:

On Debian/Ubuntu-based systems::

  $ sudo apt-get install python3-pip

On RedHat-based systems::

  $ yum install python3-pip

On Arch Linux systems::

  $ pacman -Syu python-pip

Usage
-------

To obtain help regarding the usage of any of the available FoLiA tools, please pass the ``-h`` option on the command line to the tool you intend to use. This will provide a summary on available options and usage examples. Most of the tools can run on both a single FoLiA document, as well as a whole directory of documents, allowing also for recursion. The tools generally take one or more file names or directory names as parameters.

More?
-----

Please consult the FoLiA website at https://proycon.github.io/folia for more!
