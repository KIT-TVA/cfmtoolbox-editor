from cfmtoolbox import app, CFM

from cfmtoolbox_editor.cfm_editor import CFMEditorApp


@app.command()
def edit(cfm: CFM) -> CFM:
    editor = CFMEditorApp()
    editor.start(cfm)
    print(f"Nice CFM! It even has {len(cfm.features)} features!")
    return cfm