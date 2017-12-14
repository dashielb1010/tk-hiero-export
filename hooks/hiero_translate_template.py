# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

"""
@updated_by Dashiel Bivens
@date 11/16/2016
@notes
  - Tested against tk-hiero-export v0.4.3
  - Changes from default marked with "#  CBSD Customization
                                      # ==========================="
"""


import ast

from tank import Hook
import tank.templatekey


class HieroTranslateTemplate(Hook):
    """
    Translates a template object into a hiero export string.
    """ 
    
    def execute(self, template, output_type, **kwargs):
        """
        Takes a sgtk template object as input and returns a string
        representation which is suitable for hiero exports. The hiero export templates
        contain tokens such as {shot} or {clip} which are replaced by the exporter.
        
        This hook should convert a template object with its special custom fields into
        such a string. Depending on your template setup, you may have to do different 
        steps here in order to fully convert your template. The path returned will be 
        validated to check that no leftover template fields are present and that the 
        returned path is fully understood by hiero. 
        """

        # first convert basic fields
        mapping = {
            "{Sequence}": "{sequence}",
            "{Shot}": "{shot}",
            "{name}": "{clip}",
            "{version}": "{tk_version}",
        }

        #  CBSD Customization
        # ===========================
        mapping.update({
            '{CustomEntity01}': '{CbsdSeason}',
            '{sg_sequence}': '{CbsdEpisode}',
            '{hiero_auto_version}': '{CbsdAutoVersion}',
            '{hiero_version_base_name}': '{CbsdVersionBaseName}',
        })
        # ===========================

        # see if we have a value to use for Step
        try:
            task_filter = self.parent.get_setting("default_task_filter", "[]")
            task_filter = ast.literal_eval(task_filter)
            for (field, op, value) in task_filter:
                if field == "step.Step.code":
                    mapping["{Step}"] = value
        except ValueError:
            # continue without Step
            self.parent.log_error("Invalid value for 'default_task_filter'")

        # get the string representation of the template object
        template_str = template.definition

        # simple string to string replacement
        # the nuke script name is hard coded to ensure a valid template
        if output_type == 'script':
            template_str = template_str.replace('{name}', 'scene')

        for (orig, repl) in mapping.iteritems():
            template_str = template_str.replace(orig, repl)

        # replace {SEQ} style keys with their translated string value
        for (name, key) in template.keys.iteritems():
            if isinstance(key, tank.templatekey.SequenceKey):
                # this is a sequence template, for example {SEQ}
                # replace it with ####
                template_str = template_str.replace("{%s}" % name, key.str_from_value("FORMAT:#"))

        return template_str
