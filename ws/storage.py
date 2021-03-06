from pipeline.storage import GZIPMixin, PipelineCachedStorage


class CachedStorage(GZIPMixin, PipelineCachedStorage):
    def post_process(self, paths, dry_run=False, **options):
        for name, hashed_name, processed in super().post_process(paths.copy(), dry_run, **options):
            if hashed_name != name:
                paths[hashed_name] = (self, hashed_name)
            if isinstance(processed, Exception):
                message = str(processed)
                if 'footable' in message:
                    continue  # V2 required glyphicons with a relative URL...
                if 'condBorders.png' in message:  # Firebug doesn't actually include
                    continue
            yield name, hashed_name, processed
