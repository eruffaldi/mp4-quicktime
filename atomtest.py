#!/usr/bin/env python
# encoding: utf-8
"""Unit tests for atom.py

"""

__author__ = "Steve Marshall (steve@nascentguruism.com)"
__copyright__ = "Copyright (c) 2008 Steve Marshall"
__license__ = "Python"

import atom
import os
import StringIO
import unittest

# TODO: Data atom equality based on content? Currently based on tempfile ref.

class SimpleContainerAtom(unittest.TestCase):
    type='moov'
    
    def setUp(self):
        self.atom = atom.Atom(type=self.type)
    
    def tearDown(self):
        del self.atom
    
    def testHasCorrectType(self):
        self.assertEqual(self.type, self.atom.type)
    
    def testReprIsTypeAndList(self):
        list_repr = repr([])
        expected_repr = '%s: %s' % (self.type, list_repr)
        self.assertEqual(expected_repr, repr(self.atom))
    
    # Containers are sequences
    
    def testIsContainer(self):
        self.assertEqual(True, self.atom.is_container())
    
    def testContainerIsEqual(self):
        equal_atom = atom.Atom(type=self.type)
        self.assertEqual(equal_atom, self.atom)
    
    def testContainerIsNotEqual(self):
        inequal_atom = atom.Atom(type='ftyp')
        self.assertNotEqual(inequal_atom, self.atom)
    
    def testLengthIsZero(self):
        self.assertEqual(0, len(self.atom))
    

class ContainerAtomChildManipulation(unittest.TestCase):
    type='moov'
    child_type = 'free'
    second_child_type = 'ftyp'
    
    def setUp(self):
        self.atom = atom.Atom(type=self.type)
        self.child_atom = atom.Atom(type=self.child_type)
        self.second_child_atom = atom.Atom(type=self.second_child_type)
    
    def tearDown(self):
        del self.atom
        self.child_atom = None
        self.second_child_atom = None
    
    def testAppendsFirstChild(self):
        self.atom.append(self.child_atom)
        
        self.assertEqual(1, len(self.atom))
        self.assertEqual(self.child_type, self.atom[0].type)
    
    def testInsertsOnlyChild(self):
        self.atom.insert(0, self.child_atom)
        
        self.assertEqual(1, len(self.atom))
        self.assertEqual(self.child_type, self.atom[0].type)
    
    def testInsertsBeforeAppendedChild(self):
        self.atom.append(self.second_child_atom)
        self.atom.insert(0, self.child_atom)
        
        self.assertEqual(2, len(self.atom))
        self.assertEqual(self.child_type, self.atom[0].type)
        self.assertEqual(self.second_child_type, self.atom[1].type)
    
    def testSetFirstItem(self):
        self.atom.append(self.child_atom)
        self.atom[0] = self.second_child_atom
        
        self.assertEqual(1, len(self.atom))
        self.assertEqual(self.second_child_type, self.atom[0].type)
    
    def testSetFirstItemSlice(self):
        self.atom[0:] = [self.child_atom]
        
        self.assertEqual(1, len(self.atom))
        self.assertEqual(self.child_type, self.atom[0].type)
    
    def testGetItemIndex(self):
        self.atom[0:] = [self.child_atom, self.second_child_atom]
        
        self.assertEqual(0, self.atom.index(self.child_atom))
        self.assertEqual(1, self.atom.index(self.second_child_atom))
    
    def testRemoveSoleItem(self):
        self.atom.append(self.child_atom)
        self.atom.remove(self.child_atom)
        
        self.assertEqual(0, len(self.atom))
    
    def testRemoveFirstItem(self):
        self.atom[0:] = [self.child_atom, self.second_child_atom]
        self.atom.remove(self.child_atom)
        
        self.assertEqual(1, len(self.atom))
        self.assertEqual(0, self.atom.index(self.second_child_atom))
    
    def testRemoveSlice(self):
        self.atom[0:] = [self.child_atom, self.second_child_atom]
        del self.atom[0:]
        
        self.assertEqual(0, len(self.atom))
    
    def testIterable(self):
        child_atoms = [self.child_atom, self.second_child_atom]
        self.atom[0:] = child_atoms
        
        [self.assertEqual(True, atom in child_atoms) for atom in self.atom]
    
    def testContainerWithChildrenIsEqual(self):
        child_atoms = [self.child_atom, self.second_child_atom]
        self.atom[0:] = child_atoms
        other = atom.Atom(type=self.type)
        other[0:] = child_atoms
        
        self.assertEqual(other, self.atom)
    
    def testContainerIsNotEqual(self):
        child_atoms = [self.child_atom, self.second_child_atom]
        self.atom[0:] = child_atoms
        other = atom.Atom(type=self.type)
        
        self.assertNotEqual(other, self.atom)
    

class ContainerAtomInvalidChildManipulation(unittest.TestCase):
    type = 'moov'
    
    def setUp(self):
        self.atom = atom.Atom(type=self.type)
    
    def tearDown(self):
        del self.atom
    
    # NOTE: Only testing inputs to container, as methods like index()
    #       won't find items if we only let Atoms in
    
    def testAppendOnlyAcceptsAtoms(self):
        self.assertRaises(TypeError, self.atom.append, None)
    
    def testInsertOnlyAcceptsAtoms(self):
        self.assertRaises(TypeError, self.atom.insert, 0, None)
    
    def testSetItemOnlyAcceptsAtoms(self):
        self.atom.append(atom.Atom(type='free'))
        self.assertRaises(TypeError, self.atom.__setitem__, 0, None)
    
    def testSetSliceOnlyAcceptsAtoms(self):
        self.assertRaises(TypeError, self.atom.__setslice__,
                          0, 0, [None])

class ContainerAtomInvalidDataManipulation(unittest.TestCase):
    type = 'moov'
    content = 'content'
    
    def setUp(self):
        self.atom = atom.Atom(type=self.type)
    
    def tearDown(self):
        del self.atom
    
    def testCannotWrite(self):
        self.assertRaises(ValueError, self.atom.write, self.content)
    
    def testCannotWrite(self):
        self.assertRaises(ValueError, self.atom.writelines, self.content)
    

class StoreContainerAtom(unittest.TestCase):
    type = 'moov'
    child_type = 'free'
    child_content = 'line 1\nline 2'
    
    def setUp(self):
        self.atom = atom.Atom(type=self.type)
        self.child_atom = atom.Atom(type=self.child_type)
    
    def tearDown(self):
        del self.atom
        del self.child_atom
    
    def testSaveEmpty(self):
        save_stream = StringIO.StringIO()
        self.atom.save(save_stream)
        save_stream.seek(0)
        rendered_atom = atom.render_atom_header(self.type, 0)
        
        self.assertEqual(rendered_atom, save_stream.read())
    
    def testSaveWithChild(self):
        self.atom.append(self.child_atom)
        save_stream = StringIO.StringIO()
        self.atom.save(save_stream)
        save_stream.seek(0)
        
        rendered_child = atom.render_atom_header(self.child_type, 0)
        rendered_atom = atom.render_atom_header(self.type, len(rendered_child))
        rendered_atom += rendered_child
        
        self.assertEqual(rendered_atom, save_stream.read())
    

class LoadContainerAtom(unittest.TestCase):
    type = 'moov'
    child_type = 'free'
    child_content = 'line 1'
    
    def setUp(self):
        child_atom = atom.render_atom_header(self.child_type, \
            len(self.child_content))
        child_atom += self.child_content
        
        self.rendered_atom = atom.render_atom_header(self.type, len(child_atom))
        self.rendered_atom += child_atom
        
        self.atom_stream = StringIO.StringIO()
        self.atom_stream.write(self.rendered_atom)
        self.atom_stream.seek(0)
    
    def tearDown(self):
        del self.rendered_atom
        del self.atom_stream
    
    def testAtomCanLoad(self):
        loaded_atom = atom.Atom(self.atom_stream)
    
    def testAtomHasChild(self):
        loaded_atom = atom.Atom(self.atom_stream)
        self.assertEqual(1, len(loaded_atom))
    
    def testAtomChildIsCorrect(self):
        loaded_atom = atom.Atom(self.atom_stream)
        child_atom = loaded_atom[0]
        
        self.assertEqual(self.child_type, child_atom.type)
        child_atom.seek(0)
        print child_atom._Atom__size, ":", child_atom.tell()
        print child_atom.read()
        print 'done'
        self.assertEqual(self.child_content, child_atom.read())
    

class LoadedContainerAtomChildManipulation(unittest.TestCase):
    type = 'moov'
    initial_child_type = 'free'
    initial_child_content = 'line 1'
    new_child_type = 'free'
    new_child_content = 'line 2'
    ad_hoc_type = 'free'
    ad_hoc_content = 'ad hoc'
    
    def setUp(self):
        child_atom = atom.render_atom_header(self.initial_child_type, \
            len(self.initial_child_content))
        child_atom += self.initial_child_content
        
        rendered_new_child = atom.render_atom_header(self.new_child_type, \
            len(self.new_child_content)) + self.new_child_content
        new_child_stream = StringIO.StringIO()
        new_child_stream.write(rendered_new_child)
        new_child_stream.seek(0)
        self.new_child_atom = atom.Atom(new_child_stream)
        
        rendered_atom = atom.render_atom_header(self.type, len(child_atom))
        rendered_atom += child_atom
        
        atom_stream = StringIO.StringIO()
        atom_stream.write(rendered_atom)
        atom_stream.seek(0)
        self.atom = atom.Atom(stream=atom_stream)
    
    def tearDown(self):
        del self.atom
    
    def testAppendAtom(self):
        self.atom.append(self.new_child_atom)
        
        self.assertEqual(2, len(self.atom))
        
        self.atom[0].seek(0)
        self.assertEqual(self.initial_child_content, self.atom[0].read())
        
        self.atom[1].seek(0)
        self.assertEqual(self.new_child_content, self.atom[1].read())
    


# class StoreLoadedContainerAtom(unittest.TestCase):
#     type = 'moov'
#     child_type = 'free'
#     child_initial_content = 'line 1'
#     child_new_content = 'line 2'
#     
#     def setUp(self):
#         child_atom = atom.render_atom_header(self.child_type, \
#             len(self.child_initial_content))
#         child_atom += self.child_initial_content
#         
#         self.rendered_atom = atom.render_atom_header(self.type, len(child_atom))
#         self.rendered_atom += child_atom
#         
#         init_stream = StringIO.StringIO()
#         init_stream.write(self.rendered_atom)
#         init_stream.seek(0)
#         
#         self.atom = atom.Atom(init_stream)
#         
#     
#     def tearDown(self):
#         del self.atom
#         del self.rendered_atom
#     
#     def testCanSaveLoadedAtom(self):
#         save_stream = StringIO.StringIO()
#         self.atom.save(save_stream)
#     
#     def testSavedUnchangedAtomHasCorrectContent(self):
#         save_stream = StringIO.StringIO()
#         self.atom.save(save_stream)
#         save_stream.seek(0)
#         self.assertEqual(self.rendered_atom, save_stream.read())
#     
#     def testSavesChangesToChildAtom(self):
#         print len(self.atom)
#         self.atom[0].seek(0, os.SEEK_END)
#         self.atom[0].write(self.child_new_content)
#         self.atom[0].seek(0)
#         save_stream = StringIO.StringIO()
#         self.atom.save(save_stream)
#         save_stream.seek(0)
#         
#         print save_stream.read()


class SimpleDataAtom(unittest.TestCase):
    type = 'free'
    
    def setUp(self):
        self.atom = atom.Atom(type=self.type)
    
    def tearDown(self):
        del self.atom
    
    def testHasCorrectType(self):
        self.assertEqual(self.type, self.atom.type)
    
    def testReprIsAtomType(self):
        self.assertEqual(self.type, repr(self.atom))
    
    def testIsNotContainer(self):
        self.assertEqual(False, self.atom.is_container())
    
    def testDataIsEqual(self):
        equal_atom = atom.Atom(type=self.type)
        self.assertEqual(equal_atom, self.atom)
    
    def testDataIsNotEqual(self):
        inequal_atom = atom.Atom(type='ftyp')
        self.assertNotEqual(inequal_atom, self.atom)
    
    def testCanTell(self):
        self.assertEqual(0, self.atom.tell())
    
    def testCanRead(self):
        self.atom.seek(0)
        self.assertEqual('', self.atom.read())
    
    def testLengthIsZero(self):
        self.assertEqual(0, len(self.atom))
    

class DataAtomInvalidChildManipluation(unittest.TestCase):
    type='free'
    child_type = 'free'
    
    def setUp(self):
        self.atom = atom.Atom(type=self.type)
        self.child_atom = atom.Atom(type=self.child_type)
    
    def tearDown(self):
        del self.atom
        self.child_atom = None
    
    # NOTE: Only testing inputs to container, as methods like index()
    #       won't find items if we only let Atoms in
    
    def testCannotAppend(self):
        self.assertRaises(ValueError, self.atom.append, self.child_atom)
    
    def testCannotInsert(self):
        self.assertRaises(ValueError, self.atom.insert, 0, self.child_atom)
    
    def testCannotSetSlice(self):
        self.assertRaises(ValueError, self.atom.__setslice__, 
                          0, 0, [self.child_atom])

class DataAtomManipulation(unittest.TestCase):
    type = 'free'
    content = 'content'
    
    def setUp(self):
        self.atom = atom.Atom(type=self.type)
    
    def tearDown(self):
        del self.atom
    
    def testCanWrite(self):
        self.atom.write(self.content)
    
    def testTellIsCorrectAfterWrite(self):
        self.atom.write(self.content)
        self.assertEqual(len(self.content), self.atom.tell())
    
    def testTellIsCorrectAfterSeek(self):
        self.atom.write(self.content)
        self.atom.seek(2)
        
        self.assertEqual(2, self.atom.tell())
    
    def testCanSeekRelativeToEnd(self):
        self.atom.write(self.content)
        self.atom.seek(-1, os.SEEK_END)
        self.assertEqual(len(self.content) - 1, self.atom.tell())
    
    def testCanSeekRelativeToCurrent(self):
        self.atom.write(self.content)
        self.atom.seek(2)
        self.atom.seek(2, os.SEEK_CUR)
        
        self.assertEqual(4, self.atom.tell())
    
    def testCanWriteAndReadBack(self):
        self.atom.write(self.content)
        self.atom.seek(0)
        
        self.assertEqual(self.content, self.atom.read())
    
    def testCanReadSegment(self):
        self.atom.write(self.content)
        self.atom.seek(0)
        
        self.assertEqual(self.content[:1], self.atom.read(1))
    
    def testCanReadAfterSeek(self):
        self.atom.write(self.content)
        self.atom.seek(4)
        
        self.assertEqual(self.content[4:6], self.atom.read(2))
    
    def testCanTruncate(self):
        self.atom.write(self.content)
        self.atom.seek(4)
        self.atom.truncate()
        self.atom.seek(0)
        
        self.assertEqual(self.content[:4], self.atom.read())
    
    def testCanTruncateToSize(self):
        self.atom.write(self.content)
        self.atom.truncate(4)
        self.atom.seek(0)
        
        self.assertEqual(self.content[:4], self.atom.read())
    
    def testDataIsEqual(self):
        self.atom.write(self.content)
        other = self.atom
        
        self.assertEqual(other, self.atom)
    
    def testDataIsNotEqual(self):
        self.atom.write(self.content)
        other = atom.Atom(type=self.type)
        
        self.assertNotEqual(other, self.atom)
    

class DataAtomExtendedManipulation(unittest.TestCase):
    type = 'free'
    content = 'line 1 line 1 line 1 line 1 line 1 \n' \
            + 'line 2 line 2 line 2 line 2 line 2 line 2 line 2 '
    
    def setUp(self):
        self.atom = atom.Atom(type=self.type)
    
    def tearDown(self):
        del self.atom
    
    def testCanWriteLines(self):
        self.atom.writelines(self.content)
    
    def testTellIsCorrectAfterWriteLines(self):
        self.atom.writelines(self.content)
        self.assertEqual(len(self.content), self.atom.tell())
    
    def testCanWriteLinesAndReadBack(self):
        self.atom.writelines(self.content)
        self.atom.seek(0)
        
        self.assertEqual(self.content, self.atom.read())
    
    def testCanReadLine(self):
        self.atom.write(self.content)
        self.atom.seek(0)
        
        first_line = self.content.index('\n')
        self.assertEqual(self.content[:first_line + 1], self.atom.readline())
        self.assertEqual(self.content[first_line + 1:], self.atom.readline())
    
    def testCanReadLineWithSize(self):
        self.atom.write(self.content)
        self.atom.seek(0)
        
        self.assertEqual(self.content[:4], self.atom.readline(4))
    
    def testCanReadLines(self):
        self.atom.write(self.content)
        self.atom.seek(0)
        
        self.assertEqual(self.content.splitlines(True), self.atom.readlines())
    
    def testCanReadLinesWithSize(self):
        self.atom.write(self.content)
        self.atom.seek(0)
        
        self.assertEqual(self.content.splitlines(True), self.atom.readlines(50))
    
    def testCanIterateOverLines(self):
        self.atom.write(self.content)
        self.atom.seek(0)
        
        self.assertEqual(
            [len(line) for line in self.content.splitlines(True)],
            [len(line) for line in self.atom])
    
    def testCanGetNextLine(self):
        self.atom.write(self.content)
        self.atom.seek(0)
        
        self.assertEqual(self.content.splitlines(True)[0], self.atom.next())
    

class StoreDataAtom(unittest.TestCase):
    type = 'free'
    content = 'line 1\nline 2'
    
    def setUp(self):
        self.atom = atom.Atom(type=self.type)
    
    def tearDown(self):
        del self.atom
    
    def testSaveEmpty(self):
        save_stream = StringIO.StringIO()
        self.atom.save(save_stream)
        save_stream.seek(0)
        rendered_atom = atom.render_atom_header(self.type, 0)
        
        self.assertEqual(rendered_atom, save_stream.read())
    
    def testSaveWithContent(self):
        self.atom.write(self.content)
        save_stream = StringIO.StringIO()
        self.atom.save(save_stream)
        save_stream.seek(0)
        
        rendered_atom = atom.render_atom_header(self.type, len(self.content))
        rendered_atom += self.content
        
        self.assertEqual(rendered_atom, save_stream.read())
    

class LoadSimpleDataAtom(unittest.TestCase):
    type = 'free'
    content = 'line 1\nline 2'
    
    def setUp(self):
        empty_atom = atom.render_atom_header(self.type, 0)
        self.atom_stream = StringIO.StringIO()
        self.atom_stream.write(empty_atom)
        
        content_atom = atom.render_atom_header(self.type, len(self.content))
        self.atom_stream_with_content = StringIO.StringIO()
        self.atom_stream_with_content.write(content_atom + self.content)
    
    def tearDown(self):
        del self.atom_stream
        del self.atom_stream_with_content
    
    def testHasCorrectType(self):
        data_atom = atom.Atom(self.atom_stream)
        self.assertEqual(self.type, data_atom.type)
    
    def testReprIsAtomType(self):
        data_atom = atom.Atom(self.atom_stream)
        self.assertEqual(self.type, repr(data_atom))
    
    def testIsNotContainer(self):
        data_atom = atom.Atom(self.atom_stream)
        self.assertEqual(False, data_atom.is_container())
    
    def testDataIsEqual(self):
        data_atom = atom.Atom(self.atom_stream)
        equal_atom = atom.Atom(type=self.type)
        self.assertEqual(equal_atom, data_atom)
    
    def testDataIsNotEqual(self):
        data_atom = atom.Atom(self.atom_stream)
        inequal_atom = atom.Atom(type='ftyp')
        self.assertNotEqual(inequal_atom, data_atom)
    
    def testCanTell(self):
        data_atom = atom.Atom(self.atom_stream)
        self.assertEqual(0, data_atom.tell())
    
    def testCanTellAfterSeek(self):
        data_atom = atom.Atom(self.atom_stream_with_content)
        data_atom.seek(2)
        self.assertEqual(2, data_atom.tell())
    
    def testCanTellAfterSeekRelativeToCurrent(self):
        data_atom = atom.Atom(self.atom_stream_with_content)
        data_atom.seek(3)
        data_atom.seek(-3, os.SEEK_CUR)
        self.assertEqual(0, data_atom.tell())
    
    def testCanTellAfterSeekRelativeToEnd(self):
        data_atom = atom.Atom(self.atom_stream_with_content)
        data_atom.seek(-1, os.SEEK_END)
        self.assertEqual(len(self.content) - 1, data_atom.tell())
    
    def testCanRead(self):
        data_atom = atom.Atom(self.atom_stream)
        data_atom.seek(0)
        self.assertEqual('', data_atom.read())
    
    def testLengthIsZero(self):
        data_atom = atom.Atom(self.atom_stream)
        self.assertEqual(0, len(data_atom))
    
    def testCanReadWithContent(self):
        data_atom = atom.Atom(self.atom_stream_with_content)
        data_atom.seek(0)
        self.assertEqual(self.content, data_atom.read())
    
    def testCanReadAfterSeek(self):
        data_atom = atom.Atom(self.atom_stream_with_content)
        data_atom.seek(7)
        self.assertEqual(self.content[7:], data_atom.read())
    

class ManipulateLoadedDataAtom(unittest.TestCase):
    type = 'free'
    initial_content = 'line 1'
    new_content = 'line 2'
    
    def setUp(self):
        content_atom = atom.render_atom_header(self.type, len(self.initial_content))
        self.atom_stream = StringIO.StringIO()
        self.atom_stream.write(content_atom + self.initial_content)
        self.atom = atom.Atom(self.atom_stream)
    
    def tearDown(self):
        del self.atom_stream
        del self.atom
    
    def testCanWrite(self):
        self.atom.seek(0)
        self.atom.write(self.new_content)
    
    def testReadAfterWriteIsCorrect(self):
        self.atom.seek(0)
        self.atom.write(self.new_content)
        self.atom.seek(0)
        self.assertEqual(self.new_content, self.atom.read())
    
    def testCanAppend(self):
        self.atom.seek(0, os.SEEK_END)
        self.atom.write(self.new_content)
    
    def testReadAfterAppendIsCorrect(self):
        self.atom.seek(0, os.SEEK_END)
        self.atom.write(self.new_content)
        self.atom.seek(0)
        self.assertEqual(self.initial_content + self.new_content, \
            self.atom.read())
    
    def testCanSaveAfterAppend(self):
        self.atom.seek(0, os.SEEK_END)
        self.atom.write(self.new_content)
        
        save_stream = StringIO.StringIO()
        self.atom.save(save_stream)
        save_stream.seek(0)
        
        rendered_atom = atom.render_atom_header(self.type, len(self.initial_content) + len(self.new_content))
        rendered_atom += self.initial_content + self.new_content
        
        self.assertEqual(rendered_atom, save_stream.read())
    


if __name__ == "__main__":
    unittest.main()