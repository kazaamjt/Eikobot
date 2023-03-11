# Internal developer docs

Docs for the development of eikobot itself.  

## Creating and uploading a release

```bash
python -m build
twine upload --repository pypi dist/*
```
