# `Android Debug Bridge` Profiler

This example shows how to automatically collect battery and energy metrics from
Android devices during experiment execution using ADB.

## Requirements
  - Android SDK Platform Tools installed
    - Linux:
        ```bash 
        sudo apt install android-tools-adb android-tools-fastboot
        ```
    - macOS:
        ```bash
        brew install android-platform-tools
        ```
  - Android device connected via USB or emulator running
  - USB debugging enabled on device

## Running
From the root directory of the repo, run the following command:
  ```bash
  python experiment-runner/ examples/profilers/ADB/RunnerConfig.py
  ```

## Results
The results are generated in the `examples/profilers/ADB/experiments` folder.

In case there are anomalies such as null, absent, or negative values, a report will be generated in the `examples/profilers/ADB/experiments` folder.