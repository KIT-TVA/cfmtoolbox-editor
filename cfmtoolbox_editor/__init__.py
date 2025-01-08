from cfmtoolbox import app, CFM

from cfmtoolbox_editor.cfm_editor import CFMEditorApp


@app.command()
def edit(cfm: CFM) -> CFM:
    editor = CFMEditorApp()
    return editor.start(cfm)
