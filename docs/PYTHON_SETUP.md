# Python Installation Check & Configuration

## Current System Status

### ✅ Conda Python (Active)
- **Location**: `/opt/miniconda3/bin/python`
- **Version**: Python 3.13.9 (packaged by Anaconda)
- **Status**: ✅ Currently active and being used
- **Is Conda**: Yes
- **PATH Priority**: Conda paths are in PATH (after Homebrew, but still active)

### ⚠️ Other Python Installations Found

#### Homebrew Python
- **Location**: `/opt/homebrew/bin/python3` and `/opt/homebrew/bin/python3.14`
- **Version**: Python 3.14.0
- **Status**: Installed and in PATH (before conda, but conda Python still active)
- **Risk**: Low (not currently interfering, but could if PATH changes)
- **Recommendation**: Ensure conda is initialized in shell config

#### System Python
- **Location**: `/usr/bin/python3` (macOS system Python)
- **Status**: Present but not interfering
- **Risk**: None (system Python is typically read-only and not used)

### ✅ Other Python Managers
- **pyenv**: Not installed
- **Status**: No conflicts

## Ensuring Conda-Only Usage

### Current Configuration

The system is currently configured correctly:
- ✅ Active Python is from conda (`/opt/miniconda3/bin/python`)
- ✅ Conda environment `orion` exists and uses conda Python
- ✅ PATH prioritizes conda over other installations

### Verification Commands

Check which Python is active:
```bash
which python
python --version
python -c "import sys; print(sys.executable)"
```

Verify it's conda Python:
```bash
python -c "import sys; print('Is Conda:', 'conda' in sys.executable or 'miniconda' in sys.executable or 'anaconda' in sys.executable)"
```

Check conda environment:
```bash
conda info --envs
conda activate orion
which python  # Should show /opt/miniconda3/envs/orion/bin/python
```

### Best Practices

1. **Always activate conda environment before working:**
   ```bash
   conda activate orion
   ```

2. **Verify Python source before running commands:**
   ```bash
   which python  # Should point to conda
   ```

3. **Use conda run for one-off commands:**
   ```bash
   conda run -n orion python -m src.cli --help
   ```

4. **Check PATH order:**
   ```bash
   echo $PATH | tr ':' '\n' | grep -n "conda\|python"
   ```
   Conda paths should appear before other Python installations.

### If Homebrew Python Interferes

If Homebrew Python appears in PATH before conda:

1. **Check shell configuration:**
   ```bash
   cat ~/.zshrc | grep -i python
   cat ~/.bash_profile | grep -i python
   ```

2. **Ensure conda is initialized:**
   ```bash
   conda init zsh  # or bash
   ```

3. **Re-order PATH in shell config:**
   ```bash
   # In ~/.zshrc or ~/.bash_profile
   export PATH="/opt/miniconda3/bin:$PATH"
   ```

### Recommended Shell Configuration

Add to `~/.zshrc` or `~/.bash_profile`:
```bash
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/opt/miniconda3/bin/conda' 'shell.zsh' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/opt/miniconda3/etc/profile.d/conda.sh" ]; then
        . "/opt/miniconda3/etc/profile.d/conda.sh"
    else
        export PATH="/opt/miniconda3/bin:$PATH"
    fi
fi
unset __conda_setup
# <<< conda initialize <<<

# Auto-activate orion environment (optional)
# conda activate orion
```

## Troubleshooting

### Issue: Wrong Python is active

**Solution:**
```bash
conda activate orion
which python  # Verify it's conda
```

### Issue: Homebrew Python in PATH

**Solution:**
```bash
# Check PATH
echo $PATH

# If homebrew is before conda, reorder in shell config
# Or use full path to conda Python
/opt/miniconda3/envs/orion/bin/python -m src.cli --help
```

### Issue: Multiple Python versions

**Solution:**
```bash
# Use conda run to ensure correct environment
conda run -n orion python -m src.cli --help
```

## Summary

✅ **Current Status**: System is correctly configured
- Conda Python is active
- No system Python conflicts
- Homebrew Python exists but doesn't interfere
- PATH is correctly ordered

✅ **Recommendation**: Continue using conda exclusively
- Always activate `orion` environment: `conda activate orion`
- Verify with `which python` before running commands
- Use `conda run -n orion` for scripts/automation

