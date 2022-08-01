# Wumpy-models

Fully typed, memory efficient Discord object representations.

```python
from wumpy.models import User


user = User.from_data({ ... })

print(f'{user.name}#{user.discriminator}')
```
