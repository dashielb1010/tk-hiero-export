# Copyright (c) 2014 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

from tank import Hook


class HieroResolveCustomStrings(Hook):
    """Translates a keyword string into its resolved value for a given task."""
    # cache of shots that have already been pulled from shotgun
    _sg_lookup_cache = {}

    #  CBSD Customization
    # ===========================

    def cbsd_clear_lookup_cache(self):
        # the methods that query shotgun will only happen once, but those methods get executed *even for
        # generating the preview in the GUI*. Let's make sure when we do an export, that all versions
        # are gotten again, just in case we're exporting the same shots' plates for a second time during a session.
        # Call this method during Pre-Export.
        self._sg_lookup_cache = {}

    def getCbsdElementTag(self, item):

        CBSD_TAG_SIGNATURE = 'cbsd_element_tag'
        for tag in item.tags():
            if tag.metadata().hasKey(CBSD_TAG_SIGNATURE):
                return tag

    def getAutoVersion(self, task):

        version_base_name = self.getVersionBaseName(task)

        if version_base_name not in self._sg_lookup_cache:
            shot = self.parent.execute_hook("hook_get_shot", task=task, item=task._item, data=self.parent.preprocess_data)
            filters = [
                ['project', 'is', self.parent.context.project],
                ['entity', 'is', shot],
                ['code', 'contains', version_base_name]
            ]
            fields = [
                'sg_version_number',
            ]
            previous_versions = self.parent.shotgun.find("Version", filters, fields)
            self._sg_lookup_cache[version_base_name] = previous_versions

        previous_versions = self._sg_lookup_cache[version_base_name]

        highest_available_number = 1
        for version in previous_versions:
            num = version['sg_version_number']
            if num > highest_available_number:
                highest_available_number = num + 1

        return '%s' % format(highest_available_number, "03")

    def getVersionBaseName(self, task):

        item = task._item
        element_tag = self.getCbsdElementTag(item)
        if element_tag and element_tag.metadata().hasKey('tag.version_base_name'):
            version_base_name = element_tag.metadata().value('tag.version_base_name')
            return version_base_name
        else:
            return ''

    # ===========================

    def execute(self, task, keyword, **kwargs):
        """
        The default implementation of the custom resolver simply looks up
        the keyword from the shotgun shot dictionary.

        For example, to pull the shot code, you would simply specify 'code'.
        To pull the sequence code you would use 'sg_sequence.Sequence.code'.
        """

        #  CBSD Customization
        # ===========================

        keyword_field_replacements = {
            'CbsdSeason': 'sg_sequence.Sequence.sg_season.CustomEntity01.code',
            'CbsdEpisode': 'sg_sequence.Sequence.code',
        }
        if keyword[1:-1] in keyword_field_replacements:
            keyword = "{%s}" % keyword_field_replacements[keyword[1:-1]]

        keyword_custom_logic = (
            "{CbsdAutoVersion}",
            "{CbsdVersionBaseName}"
        )

        if keyword in keyword_custom_logic:
            if keyword == keyword_custom_logic[0]:
                return self.getAutoVersion(task)
            elif keyword == keyword_custom_logic[1]:
                return self.getVersionBaseName(task)
        # ===========================

        shot_code = task._item.name()

        # grab the shot from the cache, or the get_shot hook if not cached
        sg_shot = self._sg_lookup_cache.get(shot_code)
        if sg_shot is None:
            fields = [ctf['keyword'] for ctf in self.parent.get_setting('custom_template_fields')]

            #  CBSD Customization
            # ===========================
            amended_fields = []
            for field in fields:
                if field in keyword_field_replacements:
                    amended_fields.append(keyword_field_replacements[field])
                else:
                    amended_fields.append(field)
            fields = amended_fields
            # ===========================

            sg_shot = self.parent.execute_hook(
                "hook_get_shot",
                task=task,
                item=task._item,
                data=self.parent.preprocess_data,
                fields=fields,
                upload_thumbnail=False,
            )

            self._sg_lookup_cache[shot_code] = sg_shot

        if sg_shot is None:
            raise RuntimeError("Could not find shot for custom resolver: %s" % keyword)

        # strip off the leading and trailing curly brackets
        keyword = keyword[1:-1]
        result = sg_shot.get(keyword, "")

        self.parent.log_debug("Custom resolver: %s[%s] -> %s" % (shot_code, keyword, result))

        return result
