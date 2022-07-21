
# Plugins

A description and usage for each provided plugin can be found here.

---

## CodecarbonWrapper.py

### Overview

This plugin is a wrapper for the [mlco2/codecarbon](https://github.com/mlco2/codecarbon) project. It will estimate and track carbon emissions for your experiment.

### Requirements

```bash
pip install codecarbon
```

### Usage

To simply add a CO2 data column, use the following snippet:

```python
from Plugins import CodecarbonWrapper


@CodecarbonWrapper.emission_tracker(
    country_iso_code="NLD" # your country code
)
class RunnerConfig:
    ...
```

This will add an `__co2_emissions` data column in the generated run_table.csv.

For a more fine-grained approach, the above snippet is equivalent to the following:

```python
from Plugins import CodecarbonWrapper

class RunnerConfig:

    @CodecarbonWrapper.add_co2_data_column
    def create_run_table(self):
        ...
    
    @CodecarbonWrapper.start_emission_tracker(
        country_iso_code="NLD" # your country code
    )
    def start_measurement(self, context: RunnerContext):
        ...
    
    @CodecarbonWrapper.stop_emission_tracker
    def stop_measurement(self, context: RunnerContext):
        ...
    
    @CodecarbonWrapper.populate_co2_data
    def populate_run_data(self, context: RunnerContext):
        ...
```

### Known issues

* If you encounter the error "AttributeError: Jumbotron was deprecated in dash-bootstrap-components version 1.0.0.", check [issue#319](https://github.com/mlco2/codecarbon/issues/319)
* If you encounter the error "Unable to read Intel RAPL files for CPU power : Permission denied", check [issue#244](https://github.com/mlco2/codecarbon/issues/244)

### Side notes

* To find country codes, use the ISO 3166-1 Alpha-3 code from [wikipedia](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes)
