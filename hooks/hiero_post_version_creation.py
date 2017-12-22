# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk

#  CBSD Customization
# ==============================
import os
import yaml
import traceback
# ==============================

HookBaseClass = sgtk.get_hook_baseclass()

class HieroPostVersionCreation(HookBaseClass):
    """
    Post processing of the Version entity that was created during export.
    """
    def execute(self, version_data, **kwargs):
        """
        Run following the creation of the Version entity in Shotgun. The
        provided version data is the data structure containing information
        about the Version entity, including its ID in Shotgun.

        Example version_data:

            {'code': 'Scene_v031_abc',
             'created_by': {'id': 39, 'name': 'Jeff Beeland', 'type': 'HumanUser'},
             'entity': {'id': 1166, 'name': 'ABC', 'type': 'Shot'},
             'id': 6039,
             'project': {'id': 74, 'name': 'DevWindows', 'type': 'Project'},
             'published_files': [{'id': 108,
                                  'name': 'scene_v031_ABC.mov',
                                  'type': 'PublishedFile'}],
             'sg_path_to_movie': 'd:\\shotgun\\projects\\devwindows\\sequences\\123\\ABC\\editorial\\2015_11_24\\plates\\scene_v031_ABC.mov',
             'sg_task': {'id': 2113, 'name': 'Comp', 'type': 'Task'},
             'type': 'Version',
             'user': {'id': 39, 'name': 'Jeff Beeland', 'type': 'HumanUser'}}
        """

        #  CBSD Customization
        # ==============================

        self.createShotgunVersionTempFile(version_data, kwargs.get("task"))

        # Upload thumbnail to Version
        task = kwargs.get("task")
        if task:
            item = task._item
            source = item.source()
            self.parent.execute_hook("hook_upload_thumbnail",
                                     entity=version_data,
                                     source=source,
                                     item=item,
                                     )

        # ==============================

    #  CBSD Customization
    # ==============================

    def createShotgunVersionTempFile(self, version_data, task):
        """
        If the Shotgun Version creation task was a deadline submission,
        create a tempfile that the Deadline Submission script will be
        looking for when it finishes transcoding a .mov file for
        upload to Shotgun.

        @param version_data - \b dict - The Version entity previously created in Shotgun.
        @param task - \b version_creator.ShotgunTranscodeExporter - The
        Shotgun Transcode Exporter Task for the exported item
        """
        if not task or task.shotgunVersionTempFile:
            self.parent.logger.warning("No Deadline Tempfile Attribute found on the task: %s" % str(task))
            return
        temp_file_path = task.shotgunVersionTempFile

        try:
            with open(temp_file_path, 'w+') as tf:
                tf.write(yaml.dump(version_data))
            assert os.path.exists(temp_file_path)
        except Exception as err:
            self.parent.logger.warning('Failed to write to ShotgunVersionTempFile:')
            self.parent.logger.error(traceback.format_exc())
            self.parent.logger.error(err)

    # ==============================