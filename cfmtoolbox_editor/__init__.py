from cfmtoolbox import app, CFM

@app.command()
def edit(cfm: CFM) -> CFM:
    print(f"Nice CFM! It even has {len(cfm.constraints)} constraints!")
    return cfm