import os

from sdmmlib.dscstools import DSCSTools

from src.CoreOperations.Tools.DSCSToolsHandler.MDB1Multithreaded import MDB1FilelistExtractor, MDB1Extractor
from src.CoreOperations.Tools.DSCSToolsHandler.MBEMultithreaded import MBEExtractor, MBEPacker
from src.CoreOperations.Tools.DSCSToolsHandler.ScriptMultithreaded import ScriptExtractor, ScriptPacker

class DSCSToolsHandler:
    @staticmethod
    def extractMDB1File(mdb1_path, destination_path, filepath):
        DSCSTools.extractMDB1File(mdb1_path, destination_path, filepath)

    @staticmethod
    def generateFilelistExtractor(threadpool, ops, files_to_extract, filepack, parent=None):
        return MDB1FilelistExtractor(threadpool, ops, files_to_extract, filepack, parent)

    @staticmethod
    def generateMDB1Extractor(threadpool, ops, archive_path, extract_path, parent=None):
        return MDB1Extractor(threadpool, ops, archive_path, extract_path, parent)

    @staticmethod
    def generateMBEExtractor(threadpool, ops, mbe_path, parent=None):
        return MBEExtractor(threadpool, ops, mbe_path, parent)

    @staticmethod
    def generateMBEPacker(threadpool, ops, mbe_path, parent=None):
        return MBEPacker(threadpool, ops, mbe_path, parent)

    @staticmethod
    def generateScriptExtractor(threadpool, ops, script_path, parent=None):
        return ScriptExtractor(threadpool, ops, script_path, parent)

    @staticmethod
    def generateScriptPacker(threadpool, ops, script_path, parent=None):
        return ScriptPacker(threadpool, ops, script_path, parent)
