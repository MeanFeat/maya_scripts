import maya.mel as mel
from maya.cmds import pluginInfo as pluginInfo
from maya.cmds import loadPlugin as loadPlugin

pluginFileName = 'averageVertexSkinWeightCmd.py'
if not pluginInfo(pluginFileName, q=True, l=True):
    loadPlugin(pluginFileName)


def initPaint():
    cmd = '''
  global string $avgVertexSkinWeightsBrushSel[];
  
  global proc averageVertexWeightBrush(string $context) {
      artUserPaintCtx -e -ic "init_averageVertexWeightBrush" -svc "set_averageVertexWeightBrush"
      -fc "" -gvc "" -gsc "" -gac "" -tcc "" $context;
  }
  
  global proc init_averageVertexWeightBrush(string $name) {
      global string $avgVertexSkinWeightsBrushSel[];
  
      $avgVertexSkinWeightsBrushSel = {};
      string $sel[] = `ls -sl -fl`;
      string $obj[] = `ls -sl -o`;
      $objName = $obj[0];
  
      int $i = 0;
      for($vtx in $sel) {
          string $buffer[];
          int $number = `tokenize $vtx ".[]" $buffer`;
          $avgVertexSkinWeightsBrushSel[$i] = $buffer[2];
          $i++;
          if ($number != 0)
          $objName = $buffer[0];
      }  
  }
  
  global proc set_averageVertexWeightBrush(int $slot, int $index, float $val) {
      global string $avgVertexSkinWeightsBrushSel[];
  
      if($avgVertexSkinWeightsBrushSel[0] != "") {
          if(!stringArrayContains($index, $avgVertexSkinWeightsBrushSel))
              return; 
      }
      averageVertexSkinWeight -i $index -v $val;     
  }
  '''
    mel.eval(cmd)


def paint():
    cmd = '''
  ScriptPaintTool;
  artUserPaintCtx -e -tsc "averageVertexWeightBrush" `currentCtx`;
  '''
    mel.eval(cmd)


initPaint()
