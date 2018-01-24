# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

#  UI Hook
# ===========================

import sgtk
import hiero

from sgtk.platform.qt import QtGui

from hiero.ui.FnUIProperty import UIPropertyFactory

#  CBSD Customization
# ===========================
from TagElements.constants import PLATE_TYPE, REF_TYPE, ELEMENT_TYPE_NAMES
# ===========================

HookBaseClass = sgtk.get_hook_baseclass()


class HieroCustomizeExportUI(HookBaseClass):
    """
    A hook to modify the GUI elements presented by the Shotgun Hiero Exporter
    For use in adding preset properties that could drive custom behavior in other hooks.
    """
    # Normally, the type testing these constants are used for would be handled using `isinstance`,
    # however I can't seem to use the `Application.import_module` method to access the actual classes
    # in tk-hiero-export, so going this route instead.
    _ProcessorUIName =  'ShotgunShotProcessorUI'
    _ProcessorPresetName = 'ShotgunShotProcessorPreset'

    _TranscodeUIName = 'ShotgunTranscodeExporterUI'
    _TranscodePresetName = 'ShotgunTranscodePreset'

    _AudioExportUIName = 'ShotgunAudioExporterUI'
    _AudioExportPresetName = 'ShotgunAudioPreset'

    _NukeShotExportUIName = 'ShotgunNukeShotExporterUI'
    _NukeShotExportPresetName = 'ShotgunNukeShotPreset'

    def execute(self, layout, ui_object, **kwargs):
        """
        Called when building the various UI interfaces for the Hiero Exporter.
        Allows for additional properties to be added to the presets through the GUI interface.
        """
        # Customize the UI belonging to the Shotgun Shot Processor in `sg_shot_processor.py`
        if ui_object.__class__.__name__ == self._ProcessorUIName:
            """
            Create the custom UI elements in the Shot Processor interface related to the ShotUpdater and requiring the
            CBSD Element Tag for exports
            """
            processor_ui = ui_object
            properties = processor_ui._preset.properties()

            custom_widget = QtGui.QWidget()
            custom_layout = QtGui.QHBoxLayout(custom_widget)

            # For our custom ability to throttle the "Shot Updater". Non-hook changes in `sg_shot_processor.py`
            # and `shot_updater.py` related to these presets.
            shot_updater_layout = self._build_shot_updater_widget(processor_ui,
                                                                  properties['shotgunShotCreateProperties'],
                                                                  )
            layout.addLayout(shot_updater_layout)
            # ===========================

            # proof of concept for further custom GUI properties
            custom_widget = QtGui.QWidget()
            layout.addWidget(custom_widget)
            custom_layout = QtGui.QHBoxLayout(custom_widget)

            additional_options_widget = QtGui.QWidget()
            additional_options_layout = QtGui.QFormLayout(additional_options_widget)
            additional_options_layout.addRow(QtGui.QLabel("--- Additional CBSD Options ---"))

            require_cbsd_element_tag = "The CBSD Tag is critical to updating much of the metadata on exports to " \
                                       "Shotgun, and resolving tokens such as {CbsdAutoVersion} properly. " \
                                       "Turning this off may produce unexpected behavior-- possibly critical errors."
            key = "requireCbsdElementTag"
            value = True
            label = "Require CBSD Element Tag:"
            processor_ui._require_cbsd_element_tag = UIPropertyFactory.create(type(value), key=key, value=value,
                                                                              dictionary=properties, label=label,
                                                                              tooltip=require_cbsd_element_tag
                                                                              )

            additional_options_layout.addRow(label, processor_ui._require_cbsd_element_tag)

            correct_element_type = "What element type to allow for exports. Abort if non-elements or the wrong " \
                                   "element type is found among the export selection."
            key = "correctElementType"
            value = sorted(list(ELEMENT_TYPE_NAMES.itervalues()))
            label = "Correct Element Type:"
            processor_ui._correct_element_type = UIPropertyFactory.create(type(value), key=key,
                                                                          value=value, dictionary=properties,
                                                                          label=label, tooltip=correct_element_type
                                                                          )

            additional_options_layout.addRow(label, processor_ui._correct_element_type)

            custom_layout.addWidget(additional_options_widget)

            layout.addWidget(custom_widget)

        # Customize the UI for the "Shotgun Transcode Images" export type in the `version_creator.py` module.
        elif ui_object.__class__.__name__ == self._TranscodeUIName:
            """
            Create the custom UI elements related to Colorspace Passthrough on the Transcode Task.
            """
            transcoder_ui = ui_object

            properties = transcoder_ui._preset.properties()

            passthrough_widget = QtGui.QWidget()
            passthrough_layout = QtGui.QFormLayout(passthrough_widget)

            colorspace_passthrough = """Disregard the output colorspace below and set the write node's colorspace knob
            to the setting declared in the Hiero timeline."""
            key = "colorspacePassthrough"
            value = False
            label = "Colorspace Passthrough:"
            transcoder_ui._colorspace_passthrough = UIPropertyFactory.create(type(value), key=key, value=value,
                                                                             dictionary=properties, label=label,
                                                                             tooltip=colorspace_passthrough
                                                                             )

            passthrough_layout.addRow(label, transcoder_ui._colorspace_passthrough)

            abort_if_red_clips = """Colorspace passthrough exports are not possible with RED clips. This option will
            abort the export if any RED clips are present."""
            key = "abortIfRedClips"
            value = True
            label = "Abort if RED clip(s):"
            transcoder_ui._abort_if_red_clips = UIPropertyFactory.create(type(value), key=key, value=value,
                                                                             dictionary=properties, label=label,
                                                                             tooltip=abort_if_red_clips
                                                                             )
            passthrough_layout.addRow(label, transcoder_ui._abort_if_red_clips)

            layout.addWidget(passthrough_widget)

        # Customize the UI for the "Shotgun Audio Export" in the `sg_audio_export.py` module.
        elif ui_object.__class__.__name__ == self._AudioExportUIName:
            """
            The following code is a template for adding custom options to the Audio Exporter interface, but is not
            currently being used.
            """
            # audio_exporter_ui = ui_object
            #
            # properties = audio_exporter_ui._preset.properties()
            #
            # custom_widget = QtGui.QWidget()
            # layout.addWidget(custom_widget)
            # custom_layout = QtGui.QHBoxLayout(custom_widget)
            #
            # additional_options_widget_01 = QtGui.QWidget()
            # additional_options_layout_01 = QtGui.QFormLayout(additional_options_widget_01)
            # additional_options_layout_01.addRow(QtGui.QLabel(":::: Additional Audio Export Options ::::"))
            #
            # custom_property = """Set a new custom property!"""
            # key = "customProperty01"
            # value = True
            # label = "Custom Property:"
            # audio_exporter_ui._custom_property_01 = UIPropertyFactory.create(type(value), key=key, value=value,
            #                                                              dictionary=properties, label=label,
            #                                                              tooltip=custom_property
            #                                                              )
            #
            # additional_options_layout_01.addRow(label, audio_exporter_ui._custom_property_01)
            #
            # custom_layout.addWidget(additional_options_widget_01)
            pass

        # Customize the UI for the "Shotgun Nuke Shot Export" in the `sg_nuke_shot_export.py` module.
        elif ui_object.__class__.__name__ == self._NukeShotExportUIName:
            """
            The following code is a template for adding custom options to the Nuke *Project* Export interface, but is
            not currently being used.
            """
            # nuke_exporter_ui = ui_object
            #
            # properties = nuke_exporter_ui._preset.properties()
            #
            # custom_widget = QtGui.QWidget()
            # layout.addWidget(custom_widget)
            # custom_layout = QtGui.QHBoxLayout(custom_widget)
            #
            # additional_options_widget_01 = QtGui.QWidget()
            # additional_options_layout_01 = QtGui.QFormLayout(additional_options_widget_01)
            # additional_options_layout_01.addRow(QtGui.QLabel(":::: Additional Nuke Shot Export Options ::::"))
            #
            # custom_property = """Set a new custom property!"""
            # key = "customProperty01"
            # value = True
            # label = "Custom Property:"
            # nuke_exporter_ui._custom_property_01 = UIPropertyFactory.create(type(value), key=key, value=value,
            #                                                                  dictionary=properties, label=label,
            #                                                                  tooltip=custom_property
            #                                                                  )
            #
            # additional_options_layout_01.addRow(label, nuke_exporter_ui._custom_property_01)
            #
            # custom_layout.addWidget(additional_options_widget_01)
            pass

    def initialize_properties(self, preset, **kwargs):
        """
        Allows for additional properties to be added to the presets through the GUI interface.
        Called when presets are initialized
        """
        if preset.__class__.__name__ == self._ProcessorPresetName:

            properties = preset.properties()['shotgunShotCreateProperties']

            # Use Caution. The setting the following values directly to the `preset.properties()`
            # Dictionary causes an infinite recursion when trying to save the preset for some reason...
            # the place to put them is `preset.properties()['shotgunShotCreateProperties']`
            # as we are doing here.

            #  CBSD Customization
            # ===========================
            properties["updateSgHeadIn"] = True
            properties["updateSgCutIn"] = True
            properties["updateSgCutOut"] = True
            properties["updateSgTailOut"] = True
            properties["updateSgCutDuration"] = True
            properties["updateSgWorkingDuration"] = True
            properties["tkCreateFilesystemStructure"] = True
            properties["sgCreateCut"] = True
            properties["requireCbsdElementTag"] = True
            properties["correctElementType"] = ELEMENT_TYPE_NAMES[PLATE_TYPE]
            # ===========================

            return properties

        elif preset.__class__.__name__ == self._TranscodePresetName:
            properties = preset.properties()

            properties["colorspacePassthrough"] = False
            properties["abortIfRedClips"] = True

            return properties

        elif preset.__class__.__name__ == self._AudioExportPresetName:
            properties = preset.properties()

            # properties["customProperty01"] = True

            return properties

        elif preset.__class__.__name__ == self._NukeShotExportPresetName:
            properties = preset.properties()

            # properties["customProperty01"] = True

            return properties

        return {}

    #  CBSD Customization
    # ===========================
    def _build_shot_updater_widget(self, processor_ui, properties):
        """This was written following the pattern in the CollatingExportUI object."""
        shot_updater_layout = QtGui.QFormLayout()

        sgCreateCut = """Create a Cut and CutItems in Shotgun..."""
        key = "sgCreateCut"
        value = True
        label = "Create Cut:"
        processor_ui._sgCreateCut = UIPropertyFactory.create(type(value), key=key, value=value, dictionary=properties,
                                                             label=label, tooltip=sgCreateCut)
        shot_updater_layout.addRow(label, processor_ui._sgCreateCut)

        shot_updater_layout.addRow(QtGui.QLabel("--- Frame Ranges ---"))

        sgHeadIn = """Update 'sg_head_in' on the Shot entity."""
        key = "updateSgHeadIn"
        value = True
        label = "Head In:"
        processor_ui._sgHeadInProperty = UIPropertyFactory.create(type(value), key=key, value=value,
                                                                  dictionary=properties,
                                                                  label=label, tooltip=sgHeadIn)
        shot_updater_layout.addRow(label, processor_ui._sgHeadInProperty)

        sgCutIn = """Update 'sg_cut_in' on the Shot entity."""
        key = "updateSgCutIn"
        value = True
        label = "Cut In:"
        processor_ui._sgCutInProperty = UIPropertyFactory.create(type(value), key=key, value=value,
                                                                 dictionary=properties,
                                                                 label=label, tooltip=sgCutIn)
        shot_updater_layout.addRow(label, processor_ui._sgCutInProperty)

        sgCutOut = """Update 'sg_cut_out' on the Shot entity."""
        key = "updateSgCutOut"
        value = True
        label = "Cut Out:"
        processor_ui._sgCutOutProperty = UIPropertyFactory.create(type(value), key=key, value=value,
                                                                  dictionary=properties,
                                                                  label=label, tooltip=sgCutOut)
        shot_updater_layout.addRow(label, processor_ui._sgCutOutProperty)

        sgTailOut = """Update 'sg_tail_out' on the Shot entity."""
        key = "updateSgTailOut"
        value = True
        label = "Tail Out:"
        processor_ui._sgTailOutProperty = UIPropertyFactory.create(type(value), key=key, value=value,
                                                                   dictionary=properties,
                                                                   label=label, tooltip=sgTailOut)
        shot_updater_layout.addRow(label, processor_ui._sgTailOutProperty)

        sgCutDuration = """Update 'sg_cut_duration' on the Shot entity."""
        key = "updateSgCutDuration"
        value = True
        label = "Cut Duration:"
        processor_ui._sgCutDurationProperty = UIPropertyFactory.create(type(value), key=key, value=value,
                                                                       dictionary=properties,
                                                                       label=label, tooltip=sgCutDuration)
        shot_updater_layout.addRow(label, processor_ui._sgCutDurationProperty)

        sgWorkingDuration = """Update 'sg_working_duration' on the Shot entity."""
        key = "updateSgWorkingDuration"
        value = True
        label = "Working Duration:"
        processor_ui._sgWorkingDurationProperty = UIPropertyFactory.create(type(value), key=key, value=value,
                                                                           dictionary=properties, label=label,
                                                                           tooltip=sgWorkingDuration)
        shot_updater_layout.addRow(label, processor_ui._sgWorkingDurationProperty)

        shot_updater_layout.addRow(QtGui.QLabel("--- File System ---"))

        tkCreateFilesystemStructure = """Run the Toolkit 'Create Folders' command for the Shot entity."""
        key = "tkCreateFilesystemStructure"
        value = True
        label = "Create Folders:"
        processor_ui._tkCreateFilesystemStructureProperty = UIPropertyFactory.create(type(value), key=key, value=value,
                                                                                     dictionary=properties, label=label,
                                                                                     tooltip=tkCreateFilesystemStructure)
        shot_updater_layout.addRow(label, processor_ui._tkCreateFilesystemStructureProperty)

        return shot_updater_layout

# ===========================
