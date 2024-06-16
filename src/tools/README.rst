Abbreviations
----------------


- In the context of tools refer to the following table for the full form of the abbreviation.


+-----------------+------------------------+
| Abbreviation    | Full Form              |
+-----------------+------------------------+
|  RQE            | Retriever Query Engine |
+-----------------+------------------------+


Create a new Tool
-----------------


- To create a new tool, you need to create a new directory in the `tools` directory.
- The directory name should be the name of the tool.
- The directory should contain the following files:
 - ``__init__.py`` - An empty file that tells python that the directory is a package.
 - ``tool.py`` - The main python file that contains the tool implementation. This tool should inherit from the `BaseTool` class.


- If the tool is a retriever tool, then the directory can contain the following files:
 - ``synthesizer.py``: Optional - A file that contains a custom synthesizer definition. A `llama_index` provided synthesizer can be created in the Tool class itself.
 - ``retriever.py``: Optional - A file that contains a custom retriever definition. A `llama_index` provided retriever can be created in the Tool class itself.
 - ``query_engine.py``: Optional - A file that contains a custom query engine definition. A `llama_index` provided query engine can be created in the Tool class itself.
 - ``node_postprocessors.py``: Optional - A file that defines all the different node-postprocessors, re-rankers, etc.
