# Workflow Patterns

## Sequential Workflows

For complex tasks, break operations into clear, sequential steps. It is often helpful to give Codex an overview of the process towards the beginning of SKILL.md:

```markdown
Filling a PDF form involves these steps:

1. Analyze the form (run analyze_form.py)
2. Create field mapping (edit fields.json)
3. Validate mapping (run validate_fields.py)
4. Fill the form (run fill_form.py)
5. Verify output (run verify_output.py)
```

## Conditional Workflows

For tasks with branching logic, guide Codex through decision points:

```markdown
1. Determine the modification type:
   **Creating new content?** → Follow "Creation workflow" below
   **Editing existing content?** → Follow "Editing workflow" below

2. Creation workflow: [steps]
3. Editing workflow: [steps]
```

## Error Handling in Workflows

For workflows that may fail at intermediate steps, include rollback instructions:

```markdown
## Rollback on Failure

If Step 3 fails:
1. Log the error details
2. Clean up partial outputs from Steps 1-2
3. Report failure reason to user
4. Suggest troubleshooting steps
```

## Data Flow Between Steps

For workflows where output from one step feeds into another:

```markdown
## Passing Data Between Steps

Step 1 outputs: `customer_id`, `account_status`
Step 2 requires: `customer_id` (from Step 1)
Step 3 requires: `customer_id`, `account_status` (from Steps 1-2)
```
