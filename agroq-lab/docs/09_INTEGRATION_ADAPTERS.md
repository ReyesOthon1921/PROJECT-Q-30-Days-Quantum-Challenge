# Integration Adapters

## Sensor adapter contract

```text
adapter_name
adapter_version
device_type
health status
raw payload
normalized observations
clock status
firmware version
signal quality
errors
```

## Manual import adapter

Accept CSV with:

```text
plot_id,observed_property,value,unit,observed_at,source_type,quality_flag,notes
```

## Image adapter

Store:

```text
image_id
plot_id
capture_time
camera_asset_id
position
view_direction
lighting
model_version
file_hash
```

## AI model adapter

Input:

- dataset version;
- feature schema;
- plot/time range.

Output:

- prediction;
- confidence or uncertainty;
- model version;
- explanation reference;
- validation status.

## Optimization adapter

Input:

- problem version;
- objective;
- constraints;
- resources;
- seed.

Output:

- feasibility;
- objective value;
- runtime;
- violations;
- selected actions;
- solver identity;
- computation type.

## Quantum adapter

Also record:

- provider;
- backend;
- qubit count;
- circuit depth;
- shots;
- transpiler settings;
- queue time;
- simulator or hardware;
- noise model.
