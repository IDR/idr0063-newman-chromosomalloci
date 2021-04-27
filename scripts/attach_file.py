import argparse
import omero.clients
import omero.cli
import sys
from omero_upload import upload_ln_s
from pathlib import Path

MIMETYPE = 'text/csv'
NAMESPACE = 'openmicroscopy.org/idr/analysis/original'
OMERO_DATA_DIR = '/data/OMERO'

def main(conn, args):
  path = Path(args.file)
  filename = path.name

  target_type = args.target.split(":")[0]
  target_id = args.target.split(":")[1]

  tmp = list(conn.getObjects(target_type, attributes={"id": target_id}))
  if len(tmp) == 0:
    sys.exit("Target found")
  if len(tmp) > 1:
    sys.exit("More than one Target found")
  tgt = tmp[0]

  existingfas = set(
    a.getFile().name for a in tgt.listAnnotations()
    if isinstance(a, omero.gateway.FileAnnotationWrapper))
  if filename in existingfas:
    sys.exit("File already attached.")

  print("Attaching {} to {} {} [{}]".format(path.resolve(), target_type ,tgt.getName(), tgt.getId()))
  fo = upload_ln_s(conn.c, path.resolve(), OMERO_DATA_DIR, args.mimetype)
  fa = omero.model.FileAnnotationI()
  fa.setFile(fo._obj)
  fa.setNs(omero.rtypes.rstring(args.namespace))
  fa = conn.getUpdateService().saveAndReturnObject(fa)
  fa = omero.gateway.FileAnnotationWrapper(conn, fa)
  tgt.linkAnnotation(fa)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("file", help="The file to attach.")
  parser.add_argument("target", help="The target, e.g. Screen:123")
  parser.add_argument("-m", "--mimetype", default=MIMETYPE, help="Mimetype")
  parser.add_argument("-ns", "--namespace", default=NAMESPACE, help="Namespace")

  args = parser.parse_args()

  with omero.cli.cli_login() as c:
    conn = omero.gateway.BlitzGateway(client_obj=c.get_client())
    main(conn, args)
