from mongoengine.signals import _signals

pre_soft_delete = _signals.signal('pre_soft_delete')
post_soft_delete = _signals.signal('post_soft_delete')
