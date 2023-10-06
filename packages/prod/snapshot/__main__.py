from pydo import Client
import time
import os

token = os.getenv('DO_TOKEN')
if not token:
    raise ValueError('DO_TOKEN environment variable is missing.')

client = Client(token)

def delete_snapshot(snapshot_id):
    resp = client.volume_snapshots.delete_by_id(snapshot_id=snapshot_id)
    return resp

def create_snapshot(droplet_name,volume_id):
    snapshot_name = f'{droplet_name}-{time.strftime("%Y-%m-%d_%H-%M-%S")}'
    req = {
        "name": snapshot_name
    }
    snapshot = client.volume_snapshots.create(volume_id, body=req)
    print(f"Snapshot created for Volume ID {volume_id}: {snapshot_name}")
    return snapshot

def main(args):
    if args.get("__ow_method", "").lower() == "get":
        return {"body": os.environ.get("AX_WEBHOOK_SECRET")}

    tag_name = args.get("tag")
    store_snapshot = int(args.get("store_snapshot"))

    droplets_response = client.droplets.list(tag_name=tag_name)
    droplets = droplets_response.get('droplets', [])

    for droplet in droplets:
        #droplet_id = droplet.get('id')
        droplet_name = droplet.get('name')
        droplet_volumes = droplet.get('volume_ids', [])

        for volume_id in droplet_volumes:
            create_snapshot(droplet_name,volume_id)

            list_snap = client.volume_snapshots.list(volume_id)

            try:
                store_snapshot = int(store_snapshot)
            except ValueError:
                raise SystemExit('count must be an interger')

            if store_snapshot >= list_snap['meta']['total']:
                print(f'No needs to be rotated for {droplet_name}')
            else:
                list_snapshot_sorted = sorted(
                    list_snap['snapshots'], key=lambda k: k['created_at'])
                for i in range(list_snap['meta']['total'] - store_snapshot):
                    delete_snapshot(
                        list_snapshot_sorted[i]['id'])
                    print('Snapshot ' + list_snapshot_sorted[i]['name'] +
                          ' is removed at ' +
                          time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
