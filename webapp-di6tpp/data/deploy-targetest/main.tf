resource "proxmox_vm_qemu" "targetest" {
  count = 1
  vmid = "4007"
  name = "targetest"
  target_node = "server19"
  clone = "ubuntu24"
  agent = 1
  os_type = "cloud-init"
  cores = 2
  sockets = 1
  cpu = "host"
  memory = 2048
  scsihw = "virtio-scsi-single"
  boot = "order=scsi0;ide0"
  hotplug  = "network,disk,usb"
    disks {
    scsi {
      scsi0 {
        disk  {
          size = "30G"
          storage = "local-lvm"
        }
      }
      scsi1 {
        disk  {
          size = "50G"
          storage = "local-lvm"
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
    bridge = "vmbr107"
  }
  lifecycle {
    ignore_changes = [
      network,
    ]
  }
  ipconfig0 = "ip=10.5.32.127/20,gw=10.5.47.254"
  searchdomain = "pdmfc.com"
  nameserver = "8.8.8.8"
  ciuser = "techsupport"
  sshkeys = <<EOF
${var.ssh_keys}
EOF
}
