#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# CherryMusic - a standalone music server
# Copyright (c) 2012 - 2014 Tom Wallroth & Tilman Boerner
#
# Project page:
#   http://fomori.org/cherrymusic/
# Sources on github:
#   http://github.com/devsnd/cherrymusic/
#
# CherryMusic is based on
#   jPlayer (GPL/MIT license) http://www.jplayer.org/
#   CherryPy (BSD license) http://www.cherrypy.org/
#
# licensed under GNU GPL version 3 (or later)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#

import nose
import os

from mock import *
from nose.tools import *

from cherrymusicserver.test.helpers import cherrytest, tempdir, mkpath, cherryconfig

from cherrymusicserver import log
log.setTest()

from cherrymusicserver import cherrymodel

def config(cfg=None):
    c = {'media.basedir': os.path.join(os.path.dirname(__file__), 'data_files')}
    if cfg:
        c.update(cfg)
    return c


@cherrytest(config())
@patch('cherrymusicserver.cherrymodel.os')
@patch('cherrymusicserver.cherrymodel.CherryModel.cache')
@patch('cherrymusicserver.cherrymodel.isplayable', lambda _: True)
def test_hidden_names_listdir(cache, os):
    model = cherrymodel.CherryModel()
    os.path.join = lambda *a: '/'.join(a)

    content = ['.hidden']
    cache.listdir.return_value = content
    os.listdir.return_value = content
    assert not model.listdir('')

    content = ['not_hidden.mp3']
    cache.listdir.return_value = content
    os.listdir.return_value = content
    assert model.listdir('')


@cherrytest(config({'search.maxresults': 10}))
@patch('cherrymusicserver.cherrymodel.CherryModel.cache')
@patch('cherrymusicserver.cherrymodel.cherrypy')
def test_hidden_names_search(cherrypy, cache):
    model = cherrymodel.CherryModel()

    cache.searchfor.return_value = [cherrymodel.MusicEntry('.hidden.mp3', dir=False)]
    assert not model.search('something')

    cache.searchfor.return_value = [cherrymodel.MusicEntry('not_hidden.mp3', dir=False)]
    assert model.search('something')

@cherrytest(config({'search.maxresults': 10}))
@patch('cherrymusicserver.cherrymodel.CherryModel.cache')
@patch('cherrymusicserver.cherrymodel.cherrypy')
def test_hidden_names_listdir(cherrypy, cache):
    model = cherrymodel.CherryModel()
    dir_listing = model.listdir('')
    assert len(dir_listing) == 1
    assert dir_listing[0].path == 'not_hidden.mp3'


@cherrytest(config({'media.transcode': False}))
def test_randomMusicEntries():
    model = cherrymodel.CherryModel()

    def makeMusicEntries(n):
        return [cherrymodel.MusicEntry(str(i)) for i in range(n)]

    with patch('cherrymusicserver.cherrymodel.CherryModel.cache') as mock_cache:
        with patch('cherrymusicserver.cherrymodel.CherryModel.isplayable') as mock_playable:
            mock_cache.randomFileEntries.side_effect = makeMusicEntries

            mock_playable.return_value = True
            eq_(2, len(model.randomMusicEntries(2)))

            mock_playable.return_value = False
            eq_(0, len(model.randomMusicEntries(2)))


@cherrytest({'media.transcode': False})
def test_isplayable():
    """ files of supported types should be playable if they exist and have content """
    model = cherrymodel.CherryModel()

    with patch(
        'cherrymusicserver.cherrymodel.CherryModel.supportedFormats', ['mp3']):

        with tempdir('test_isplayable') as tmpdir:
            mkfile = lambda name, content='': mkpath(name, tmpdir, content)
            mkdir = lambda name: mkpath(name + '/', tmpdir)

            with cherryconfig({'media.basedir': tmpdir}):
                isplayable = model.isplayable
                assert isplayable(mkfile('ok.mp3', 'content'))
                assert not isplayable(mkfile('empty.mp3'))
                assert not isplayable(mkfile('bla.unsupported', 'content'))
                assert not isplayable(mkdir('directory.mp3'))
                assert not isplayable('inexistant')


@cherrytest({'media.transcode': True})
def test_is_playable_by_transcoding():
    """ filetypes should still be playable if they can be transcoded """
    from audiotranscode import AudioTranscode

    with patch('audiotranscode.AudioTranscode', spec=AudioTranscode) as ATMock:
        ATMock.return_value = ATMock
        ATMock.availableDecoderFormats.return_value = ['xxx']
        with tempdir('test_isplayable_by_transcoding') as tmpdir:
            with cherryconfig({'media.basedir': tmpdir}):
                track = mkpath('track.xxx', parent=tmpdir, content='xy')
                model = cherrymodel.CherryModel()
                ok_(model.isplayable(track))


if __name__ == '__main__':
    nose.runmodule()
