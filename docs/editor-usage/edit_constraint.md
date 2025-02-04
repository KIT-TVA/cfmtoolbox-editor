To delete a constraint from your feature model in the CFM Toolbox Editor, follow these steps:

**Select the Constraint in the Constraints Panel**

In the Constraints Panel in the editor, locate and select the constraint you want to edit.
![Context Menu](/images/context_menu.png)

**2. Click the Edit Icon**

Once the constraint is selected, click the Edit Icon (usually represented by a pencil or edit symbol) in the Constraints Panel.

**3. Modify Feature Details**

In the edit dialog, you can make the following changes:
1. First Feature: Update the first feature involved in the constraint.
2. Cardinality for First Feature: Adjust the cardinality for the first feature (e.g., 1..1, 0..*, etc.).
3. Constraint Type: Change the type of constraint (e.g., requires, excludes, etc.).
4. Second Feature: Update the second feature involved in the constraint.
5. Cardinality for Second Feature: Adjust the cardinality for the second feature.
Click "Save" to confirm your changes.

![Context Menu](/images/edit_constraint.png)

# Notes

**Validation:** The editor will validate the updated constraint to ensure it does not conflict with existing constraints or feature relationships.

**Impact:** Editing a constraint may affect the validity of your feature model. Ensure that the changes align with your model's requirements.

**Undo:** If you make a mistake, you can use the Undo option (Ctrl+Z or Cmd+Z) to revert the changes.

# Example

Here’s an example of how a constraint might look before and after editing:

**Before**

``` Shell
Feature A (1..1) requires Feature B (1..1)
```

**After Editing**

``` Shell
Feature X (0..1) excludes Feature Y (0..*)
```
