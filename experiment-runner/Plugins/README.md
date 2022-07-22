
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

To simply measure CO2 emissions (kg) and total energy consumed (kWh) and append them as data columns, use the following snippet:

```python
from Plugins import CodecarbonWrapper
from Plugins.CodecarbonWrapper import DataColumns as CCDataCols

@CodecarbonWrapper.emission_tracker(
    data_columns=[CCDataCols.EMISSIONS, CCDataCols.ENERGY_CONSUMED],
    country_iso_code="NLD" # your country code
)
class RunnerConfig:
    ...
```

This will add `codecarbon__emissions` and `codecarbon__energy_consumed` data columns in the generated run_table.csv.

For a more fine-grained approach, the above snippet is equivalent to the following:

```python
from Plugins import CodecarbonWrapper
from Plugins.CodecarbonWrapper import DataColumns as CCDataCols

class RunnerConfig:

    @CodecarbonWrapper.add_data_columns([CCDataCols.EMISSIONS, CCDataCols.ENERGY_CONSUMED])
    def create_run_table_model(self):
        ...
    
    @CodecarbonWrapper.start_emission_tracker(
        country_iso_code="NLD" # your country code
    )
    def start_measurement(self, context: RunnerContext):
        ...
    
    @CodecarbonWrapper.stop_emission_tracker
    def stop_measurement(self, context: RunnerContext):
        ...
    
    @CodecarbonWrapper.populate_data_columns
    def populate_run_data(self, context: RunnerContext):
        ...
```

* For the description of the "emissions.csv" that is generated per variation, check [codecarbon documentation](https://mlco2.github.io/codecarbon/output.html#output).

### Known issues

* If you encounter the error "AttributeError: Jumbotron was deprecated in dash-bootstrap-components version 1.0.0.", check [issue#319](https://github.com/mlco2/codecarbon/issues/319)
* If you encounter the error "Unable to read Intel RAPL files for CPU power : Permission denied", check [issue#244](https://github.com/mlco2/codecarbon/issues/244)

### Side notes

* To find country codes, use the ISO 3166-1 Alpha-3 code from [wikipedia](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes)
