resource "proxmox_vm_qemu" "__VMNAME__" {
  count = 1
  vmid = "__VMID__"
  name = "__VMNAME__"
  target_node = "__HOST__"
  clone = "__TEMPLATE__"
  agent = 1
  os_type = "cloud-init"
  cores = __VMCPU__
  sockets = 1
  cpu = "host"
  memory = __VMMEM__
  scsihw = "virtio-scsi-single"
  boot = "order=scsi0;net0"
  hotplug  = "network,disk,usb"
  disks {
    scsi {
      scsi0 {
        disk  {
          size = "__VMDISK01__G"
          storage = "__VMDISK01LOC__"
        }
      }
    }
    ide{
      ide0 {
        cloudinit {
          storage = "local-lvm"
        }
      }
    }
  }
  network {
    model = "virtio"
    bridge = "__VMBR__"
  }
  lifecycle {
    ignore_changes = [
      network,
    ]
  }
  ipconfig0 = "ip=__VMIP__/__VMCIDR__,gw=__VMGW__"
  searchdomain = "pdmfc.com"
  nameserver = "8.8.8.8"
  ciuser = "techsupport"
  sshkeys = <<EOF
${var.ssh_keys}
EOF
}