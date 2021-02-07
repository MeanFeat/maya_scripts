import collections
import winsound
from maya import cmds, mel
from core import file_util
from core.debug import fail_exit

ProgressTuple = collections.namedtuple('ProgressWindow', ['window', 'control'])


class AnimLayer:

    def __init__(self, name):
        if cmds.animLayer(name, query=True, exists=True):
            print(name + ' already exists')
            self.scene_name = name
        else:
            self.scene_name = cmds.animLayer(name, override=False)

    def add_rotation(self, obj_name):
        cmds.animLayer(self.scene_name, edit=True, attribute=obj_name + '.rx')
        cmds.animLayer(self.scene_name, edit=True, attribute=obj_name + '.ry')
        cmds.animLayer(self.scene_name, edit=True, attribute=obj_name + '.rz')

    def mute(self, m):
        cmds.animLayer(self.scene_name, edit=True, mute=m)


def get_text_name(layer):
    layer_tok = layer.split('_')
    layer_tok.pop()
    layer_name = ''
    for s in layer_tok:
        layer_name += s
        layer_name += '_'
    return layer_name[:len(layer_name) - 1]


def get_frame_range(sel):
    if sel is None:
        return ''
    split_name = sel.split('_')
    end_frame = split_name[-1]
    end_frame = end_frame.replace("f", "")
    return end_frame


def select_layer_objects():
    mel.eval('string $layers[]={"' + get_selected_layers()[0] + '"};layerEditorSelectObjectAnimLayer($layers);')


def get_parent_layer(layer):
    return cmds.animLayer(layer, q=True, parent=True)


def get_ancestor_layers(item, layers):
    done = False
    while not done:
        done = True
        item = get_parent_layer(item)
        if item != 'BaseAnimation':
            layers.append(item)
            done = False
    return layers


def get_child_layers(item, layers):
    children = cmds.animLayer(item, q=True, children=True)
    if children is not None:
        for c in children:
            layers.append(c)
    return layers


def duplicate_under_selection():
    sel = get_selected_layers()
    for s in range(0, len(sel) - 1):
        cmds.animLayer(cmds.animLayer(copy=sel[-1]), edit=True, parent=sel[s])


def select_layer_node(layer):
    cmds.select(layer, replace=True, noExpand=True)
    print cmds.ls(selection=True)


def get_selected_layer_node(layer):
    cmds.select(layer, replace=True, noExpand=True)
    sel = cmds.ls(selection=True)
    return sel[0]


def get_selected_layers():
    layers = []
    for item in cmds.ls(type='animLayer'):
        if cmds.animLayer(item, q=True, selected=True):
            layers.append(item)
    return layers


def find_replace_in_name(find, replace_with):
    for layer in get_selected_layers():
        cmds.rename(layer, layer.replace(find, replace_with))


def try_find_replace():
    find_replace_in_name(cmds.textField('FindField', query=True, text=True),
                         cmds.textField('ReplaceField', query=True, text=True))


def try_add_fps_attr():
    for layer in get_selected_layers():
        add_fps_attribute(layer)


def sort_layers_alphabetically():
    layers = get_selected_layers()
    layers.sort()
    for layer_index in range(1, len(layers)):
        cmds.animLayer(layers[layer_index], edit=True, moveLayerAfter=layers[layer_index - 1])


def play_layers():
    for layer in get_selected_layers():
        update_layer(layer)
        cmds.currentTime(0)
        if get_frame_range(layer).isdigit():
            cmds.play(forward=True, wait=True)


def playblast_layer(layer):
    path = file_util.get_file_path() + "/PlayBlast/"
    file_util.verify_directory(path)
    file_name = path + get_text_name(layer)
    playblast_settings = 'playblast  -format avi -filename "' + file_name + '.avi" -forceOverwrite -sequenceTime 0 ' \
                                                                            '-clearCache 1 -viewer 0 -showOrnaments 1 ' \
                                                                            '-fp 4 -percent 50 -compression "MS-CRAM" ' \
                                                                            '-quality 100; '
    mel.eval(playblast_settings)


def playblast_selected():
    for layer in get_selected_layers():
        update_layer(layer)
        if get_frame_range(layer).isdigit():
            playblast_layer(layer)


def layer_rename_window():
    rename_window = cmds.window(title="LayerRename", iconName='LayerRename', resizeToFitChildren=True, te=300, le=1400,
                                widthHeight=(50, 50))
    cmds.columnLayout(adjustableColumn=True)
    cmds.text(label='Find')
    cmds.textField('FindField', width=50)
    cmds.text(label='Replace')
    cmds.textField('ReplaceField', width=50, enterCommand='try_find_replace()', alwaysInvokeEnterCommandOnReturn=True)
    cmds.button(label='Replace', command='try_find_replace()')
    cmds.text(label='Prefix')
    cmds.textField('Prefix', width=50)
    cmds.text(label='Suffix')
    cmds.textField('Suffix', width=50, enterCommand='try_name_after_parent()', alwaysInvokeEnterCommandOnReturn=True)
    cmds.button(label='Rename', command='try_name_after_parent()')
    cmds.button(label='CopyUnder', command='duplicate_under_selection()')
    cmds.button(label='Add Fps Attribute', command='try_add_fps_attr()')
    cmds.setParent('..')
    cmds.showWindow(rename_window)


def get_selected_or_all_layers():
    selected = get_selected_layers()
    if len(selected) == 0:
        selected = cmds.ls(type='animLayer')
    return selected


def try_name_after_parent():
    for layer in get_selected_layers():
        par = cmds.animLayer(layer, query=True, parent=True)
        if par != 'BaseAnimation':
            cmds.rename(layer, cmds.textField('Prefix', query=True, text=True)
                        + get_text_name(par) + cmds.textField('Suffix', query=True, text=True))


def expand_layer(layer):
    if cmds.animLayer(layer, query=True, children=True):
        mel.eval('animLayerExpandCollapseCallback "' + layer + '" 1;')


def collapse_layer(layer):
    if cmds.animLayer(layer, query=True, children=True):
        mel.eval('animLayerExpandCollapseCallback "' + layer + '" 0;')


def expand_selected_layers():
    for layer in get_selected_or_all_layers():
        expand_layer(layer)


def collapse_slected_layers():
    for layer in get_selected_or_all_layers():
        collapse_layer(layer)


def add_fps_attribute(layer):
    select_layer_node(layer)
    cmds.addAttr(longName="fps", attributeType="enum", enumName="30 fps:60 fps:", keyable=True)


def get_fps_attribute(layer):
    if cmds.attributeQuery('fps', node=layer, exists=True):
        return cmds.getAttr(layer + ".fps", asString=True)
    else:
        return "30 fps"


def create_script_job():
    return cmds.scriptJob(e=("animLayerRefresh", update_selected_layer), killWithScene=True, compressUndo=True)


def update_selected_layer():
    for item in cmds.ls(type='animLayer'):
        if cmds.animLayer(item, q=True, selected=True):
            update_layer(item)


def update_layer(layer):
    unmute = []
    for item in cmds.ls(type='animLayer'):
        if item == layer:
            if get_frame_range(item).isdigit():
                update_fps(get_fps_attribute(item))
                cmds.playbackOptions(max=get_frame_range(item))
            unmute.append(item)
            unmute = get_ancestor_layers(item, unmute)
            unmute = get_child_layers(item, unmute)
        elif item != 'BaseAnimation':
            cmds.setAttr(item + ".lock", 1)
            cmds.setAttr(item + ".mute", 1)
    for u in unmute:
        cmds.setAttr(u + ".mute", 0)
        cmds.setAttr(u + ".lock", 0)


def update_fps(string):
    cmds.currentUnit(time='ntsc')
    if string == "60 fps":
        cmds.currentUnit(time='ntscf')


def select_export_joints():
    cmds.select('Rig:root', hi=True)
    export_joints = cmds.ls(selection=True, type='joint')
    cmds.select(export_joints)


def get_export_settings(layer, start=None, end=None, file_name=''):
    mel.eval('FBXExportBakeComplexAnimation -v 1;')
    minimum = str(0) if start is None else str(start)
    maximum = 1
    layer_frame_range = get_frame_range(layer)
    if layer_frame_range.isdigit():
        maximum = layer_frame_range
    if end is not None:
        maximum = str(end)
    mel.eval("FBXExportBakeComplexStart -v " + minimum)
    mel.eval("FBXExportBakeComplexEnd -v " + maximum)
    if file_name is None or len(file_name) == 0:
        file_name = get_text_name(layer)
    path = file_util.get_file_path() + "/FBX/"
    file_util.verify_directory(path)
    return 'FBXExport -f "' + path + file_name + '.fbx" -s;'


def is_exportable(item):
    return get_frame_range(item).isdigit()


def export_layer(settings):
    orig_selection = cmds.ls(selection=True)
    select_export_joints()
    mel.eval(settings)
    cmds.select(orig_selection)


def export_selected_layers():
    selected = get_selected_layers()
    if cmds.animLayer(get_parent_layer(selected[0]), query=True, baseAnimCurves=True) is not None:
        result = cmds.confirmDialog(title='Warning:', message="BaseAnim layer not empty", button=['Continue', 'Cancel'])
        if result == 'Cancel':
            fail_exit('Export canceled because base anim layer is not empty')
    prog = create_progress_window(len(selected))
    for item in selected:
        cmds.progressBar(prog.control, edit=True, step=1)
        if is_exportable(item):
            progress_status = get_text_name(item) + '...'
            cmds.window(prog.window, edit=True, title=progress_status)
            update_layer(item)
            export_layer(get_export_settings(item))
    cmds.deleteUI(prog.window)
    winsound.PlaySound("SystemExit", winsound.SND_ALIAS)


def export_layer_range(start, end, name):
    cmds.playbackOptions(min=start, max=end)
    export_layer(get_export_settings(None, start, end, name))
    update_selected_layer()


def export_all():
    for item in cmds.ls(type='animLayer'):
        if item != 'BaseAnimation':
            if is_exportable(item):
                update_layer(item)
                export_layer(get_export_settings(item))


def try_export_range():
    start = cmds.intFieldGrp('rangeFields', query=True, value1=True)
    end = cmds.intFieldGrp('rangeFields', query=True, value2=True)
    name = cmds.textField('nameField', query=True, text=True)
    if start > end:
        fail_exit("Range start must be larger than end")
    if len(name) == 0:
        fail_exit("Name not valid")
    export_layer_range(start, end, name)


def export_range_window():
    window = cmds.window(title="Export Layer Range", iconName='Export Layer Range', resizeToFitChildren=True,
                         te=300, le=1400, widthHeight=(50, 50))
    cmds.columnLayout(adjustableColumn=True)
    cmds.intFieldGrp('rangeFields', numberOfFields=2, label='Range', value1=0, value2=20, columnAlign2=('Left', 'Left'))
    cmds.textField('nameField', width=50)
    cmds.button(label='Export', command='try_export_range()')
    cmds.setParent('..')
    cmds.showWindow(window)


def create_progress_window(size):
    win = cmds.window(title='Exporting Layers', toolbox=True)
    cmds.columnLayout()
    progress_window = ProgressTuple(win, cmds.progressBar(maxValue=size, width=400))
    cmds.showWindow(progress_window.window)
    return progress_window
