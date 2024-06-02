## Ansible для раскатки инфры

### Начало работы

Установить роли
```bash
ansible-galaxy -r requirements.yml
```

Для доступа к тачке нужно [экспортнуть ключи](https://yandex.cloud/ru/docs/compute/operations/vm-connect/os-login-export-certificate).
Затем нужно добавить ключ в ssh-agent'а и сходить на тачку один раз.

#### TLDR

```bash
mkdir ~/.ssh/yc

yc organization-manager organization list # ищем здесь organization-salos и берем id

yc compute ssh certificate export \
    --organization-id <идентификатор_организации> \
    --directory ~/.ssh/yc

ssh -i ~/.ssh/yc/<имя ключа> [логин в клауде]@158.160.151.53 # ip первой тачки
```

### Как налить инфру

```bash
ansible-playbook -i inventories/ya-cloud.yml -v playbooks/deploy-infra.yml
```
