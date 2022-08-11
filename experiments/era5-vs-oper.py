import tensorflow as tf
from keras import backend as K
from tensorflow.keras.layers import Dense, Flatten, Input, Reshape
from tensorflow.keras.models import Sequential

import climetlab as cml

request = dict(
    date="20220101/to/20220131",
    levtype="sfc",
    param="2t",
    grid="1/1",
)

ds1 = cml.load_source("mars", **request)
ds2 = cml.load_source(
    "cds",
    dataset="reanalysis-era5-single-levels",
    product_type="reanalysis",
    **request,
)

shape = ds1[0].shape


def match_other(i):
    return ds2[i].to_numpy() - ds1[i].to_numpy()


input = ds1.to_tfdataset(labels=match_other)

print(shape)
# shape = tf1.element_spec.shape
# shape=(36,19)

model = Sequential()
model.add(Input(shape=(shape[-2], shape[-1])))
model.add(Flatten())
model.add(Dense(64, activation="sigmoid"))
model.add(Dense(64, activation="sigmoid"))
model.add(Dense(shape[-2] * shape[-1]))
model.add(Reshape(target_shape=(shape[-2], shape[-1])))

model.compile(
    optimizer="adam",
    loss="mean_squared_error",
    metrics=["mean_squared_error"],
)


print(model.summary())
model.fit(
    input,
    epochs=10,
    verbose=1,
    use_multiprocessing=True,
    workers=10,
)
