# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank import Hook

#  CBSD Customization
# ==============================
import re
import traceback
from messaging import showError
# ==============================

class HieroGetShot(Hook):
    """
    Return a Shotgun Shot dictionary for the given Hiero items
    """

    #  CBSD Customization
    # ==============================
    _cbsd_shot_convention_template = 'hiero_shot_convention'
    _cbsd_shot_convention_re = None
    # ==============================

    def execute(self, task, item, data, **kwargs):
        """
        Takes a hiero.core.TrackItem as input and returns a data dictionary for
        the shot to update the cut info for.
        """

        # get the parent entity for the Shot
        parent = self.get_shot_parent(item.parentSequence(), data)

        # shot parent field
        parent_field = "sg_sequence"

        # grab shot from Shotgun
        sg = self.parent.shotgun
        filter = [
            ["project", "is", self.parent.context.project],
            [parent_field, "is", parent],
            ["code", "is", item.name()],
        ]

        # default the return fields to None to use the python-api default
        fields = kwargs.get("fields", None)
        shots = sg.find("Shot", filter, fields=fields)
        if len(shots) > 1:
            # can not handle multiple shots with the same name
            raise StandardError("Multiple shots named '%s' found", item.name())
        if len(shots) == 0:
            # create shot in shotgun

            #  CBSD Customization
            # ==============================
            scene_code = self.get_scene_code(item.name())
            scene = self.get_scene(scene_code)
            # ==============================

            shot_data = {
                "code": item.name(),
                parent_field: parent,
                "project": self.parent.context.project,
                #  CBSD Customization
                # ==============================
                'sg_scene': scene,
                # ==============================
            }
            shot = sg.create("Shot", shot_data, return_fields=fields)
            self.parent.log_info("Created Shot in Shotgun: %s" % shot_data)
        else:
            shot = shots[0]

        # update the thumbnail for the shot
        upload_thumbnail = kwargs.get("upload_thumbnail", True)
        if upload_thumbnail:
            self.parent.execute_hook(
                "hook_upload_thumbnail",
                entity=shot,
                source=item.source(),
                item=item,
                task=kwargs.get("task")
            )

        return shot

    def get_shot_parent(self, hiero_sequence, data, **kwargs):
        """
        Given a Hiero sequence and data cache, return the corresponding entity
        in Shotgun to serve as the parent for contained Shots.

        :param hiero_sequence: A Hiero sequence object
        :param data: A dictionary with cached parent data.

        The data dict is typically the app's `preprocess_data` which maintains
        the cache across invocations of this hook.
        """

        # stick a lookup cache on the data object.
        if "parent_cache" not in data:
            data["parent_cache"] = {}

        if hiero_sequence.guid() in data["parent_cache"]:
            return data["parent_cache"][hiero_sequence.guid()]

        # parent not found in cache, grab it from Shotgun
        sg = self.parent.shotgun

        filter = [
            ["project", "is", self.parent.context.project],
            ["code", "is", hiero_sequence.name()],
        ]

        # the entity type of the parent.
        par_entity_type = "Sequence"

        #  CBSD Customization
        # ==============================
        try:
            assert self.parent.context.entity and self.parent.context.entity['type'] == par_entity_type
        except AssertionError:
            message = "CBSD Error: Hiero was not Launched against the correct entity type: '%s'. Exporting to " \
                      "Shotgun is disabled!" % par_entity_type
            showError(message)
            raise Exception(message)

        filter = [
            ['id', 'is', self.parent.context.entity['id']]
        ]
        # ==============================

        parents = sg.find(par_entity_type, filter)
        if len(parents) > 1:
            # can not handle multiple parents with the same name
            raise StandardError(
                "Multiple %s entities named '%s' found" %
                (par_entity_type, hiero_sequence.name())
            )

        if len(parents) == 0:
            # create the parent in shotgun
            par_data = {
                "code": hiero_sequence.name(),
                "project": self.parent.context.project,
            }
            parent = sg.create(par_entity_type, par_data)
            self.parent.log_info(
                "Created %s in Shotgun: %s" % (par_entity_type, par_data))
        else:
            parent = parents[0]

        # update the thumbnail for the parent
        upload_thumbnail = kwargs.get("upload_thumbnail", True)
        if upload_thumbnail:
            self.parent.execute_hook(
                "hook_upload_thumbnail",
                entity=parent,
                source=hiero_sequence,
                item=None
            )

        # cache the results
        data["parent_cache"][hiero_sequence.guid()] = parent

        return parent

    #  CBSD Customization
    # ==============================
    def get_scene_code(self, shot_code):
        """
        Parse the a shot code for the middle scene digits in the SHOT_CONVENTION

        @param shot_code - \b str - the shot code
        @return scene_code - \b str - the portion of the shot code corresponding to its scene
        """
        if not self.__class__._cbsd_shot_convention_re:
            try:
                shot_convention_template = self.parent.engine.sgtk.templates[self._cbsd_shot_convention_template]
                fields = self.parent.context.as_template_fields(shot_convention_template)
                convention_pattern = shot_convention_template.apply_fields(fields)
            except KeyError:
                self.parent.logger.error("The template '%s' was not found in the Toolkit Configuration. "
                                         "It is required in order for Scene codes to resolve appropriately. "
                                         "Its definition must return a valid regular expression pattern, with a "
                                         "'scene' capture group.")
                raise
            try:
                self.__class__._cbsd_shot_convention_re = re.compile(convention_pattern)
            except:
                self.parent.logger.error("CBSD ERROR: The '%s' template definition is not a valid re pattern."
                                  % self._cbsd_shot_convention_template)
                raise

        else:
            scene_code = ''
            match = self.__class__._cbsd_shot_convention_re.match(shot_code)

            if not match:
                self.parent.logger.warning(
                    "The Shot code, '%s' was not matched to the resolved shot convention: %s"
                    % (shot_code, self.__class__._cbsd_shot_convention_re.pattern))
            else:
                scene_code = match.groupdict().get('scene')
            return scene_code

    def get_scene(self, scene_code):
        """
        Query shotgun for the scene with the corresponding code, and create one if necessary.

        @param scene_code - \b str - the scene code
        @param shotgun - a Shotgun API instance
        @return \b scene_entity - \b dict - the Shotgun Scene entity matching the scene code.
        """
        if not scene_code:
            return
        self.parent.logger.debug("Checking Shotgun for Existing Scene, '%s'..." % scene_code)
        scene_entities = self.parent.shotgun.find("Scene", [
            ['project', 'is', self.parent.context.project],
            ['code', 'is', scene_code]], ['code'])

        if not scene_entities:
            scene_entity = self.parent.shotgun.create("Scene", {'code': scene_code, 'project': self.parent.context.project})
            self.parent.logger.debug("Scene not found. Created: %s" % scene_entity)
        else:
            scene_entity = scene_entities[0]
            self.parent.logger.debug("Scene found: %s" % scene_entity)
        return scene_entity
    # ==============================

