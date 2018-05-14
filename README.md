## pynsxt
python tool for NSX-T.
This tool can allow us to do with NSX-T configuration.
pynsxt reads a configuration file and create/update/delete based on the tasks in the configuration file.

## Example

When you want to create and delete transport zone, please create the following yaml file.

```
env:
  nsxManager:
    ip: '10.16.181.153'
    username: 'admin'    
    password: 'VMware1!' 
      
# action: create,update,delete
tasks:
  - module: 'TransportZone'
    action: 'create'
    data:
      display_name: 'OverlayTZ'
      host_switch_mode: 'STANDARD'
      host_switch_name: 'overlayNVDS'
      transport_type: 'OVERLAY'
  - module: 'TransportZone'
    action: 'delete'
    data:
      display_name: 'OverlayTZ'
```

## License
MIT
