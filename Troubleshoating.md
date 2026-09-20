# Troubleshooting

## 1. Python Package Installation Error

When installing and setting up `experiment-runner`, one common issue is running:

```bash
pip3 install -r requirments.txt
```

and getting the following error:

```text
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try apt install
    python3-xyz
```

Some Linux distributions (especially Ubuntu 24+, Debian, and Fedora) protect the system Python installation to avoid breaking system packages.

### Solution

Run:

```bash
pip3 install -r requirments.txt --break-system-packages
```

### Alternative

Use a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 2. EnergiBridge / JoularCore Permission Error

When using EnergiBridge or JoularCore on Linux systems (especially AMD CPUs), you may encounter the following error when running the experiment:

```text
thread 'main' (33575) panicked at src/cpu/amd.rs:20:76:
called `Result::unwrap()` on an `Err` value: Os { code: 13, kind: PermissionDenied, message: "Permission denied" }
note: run with `RUST_BACKTRACE=1` environment variable to display a backtrace
```

The Rust profiler is trying to access low-level CPU energy counters (MSR / RAPL interfaces), but Linux blocks access for normal users.

### Solution

#### 1. Load the MSR Kernel Module

Run:

```bash
sudo modprobe msr
```

Then verify the device exists:

```bash
ls /dev/cpu/0/msr
```

Expected output:

```text
/dev/cpu/0/msr
```

If the file does not exist, the kernel module did not load correctly.

---

#### 2. Check MSR Permissions

Run:

```bash
ls -l /dev/cpu/0/msr
```

If you see something similar to:

```text
crw------- 1 root root
```

then only the root user can access the CPU energy counters.

---

#### 3. Grant Read Permissions

Run:

```bash
sudo chmod o+r /dev/cpu/*/msr
```

This temporarily allows non-root users to read the MSR registers.

---

#### If Nothing Works

Some Linux systems completely block low-level profiling access.

Run:

```bash
cat /proc/sys/kernel/perf_event_paranoid
```

If the value is:

```text
2
3
4
```

then Linux is blocking low-level performance counters.

#### Temporary Fix

Run:

```bash
echo -1 | sudo tee /proc/sys/kernel/perf_event_paranoid
```

This temporarily lowers the kernel restrictions and allows profiling tools to access hardware counters.
