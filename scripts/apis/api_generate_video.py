import matplotlib.image as mpimg
import matplotlib.gridspec as gridspec
import multiprocessing
import logging
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import interpolate

df = pd.read_csv('./o_csv/out.csv', sep=',', index_col='id', dtype={'img_name': str})

api = 'azure'
# get chosen api data
api_data = df.loc[df.source == api].sort_values('img_name')

fig = plt.figure(figsize=(15, 6))
gs = gridspec.GridSpec(2, 2)
ax1 = plt.subplot(gs[0, 0])
ax2 = plt.subplot(gs[1, :])
ax3 = plt.subplot(gs[0, 1])
ax1.axis('off')
ax3.grid(True)
ax2.grid(True, axis='y')
ax2.set_axisbelow(True)
ax3.set_axisbelow(True)
ax2.get_xaxis().set_visible(False)

img = mpimg.imread('./video/in/001.png')

emotion_cols = api_data.columns[2:]
for emo in emotion_cols:
    api_data[emo] = api_data[emo].rolling(7).mean()

api_data = api_data.fillna(0)

img = ax1.imshow(img)
chart = ax2.plot(api_data.img_name, api_data.iloc[:, 2:])
line, = ax2.plot([0, 0], [0, 100], '--', linewidth=1, color='grey', zorder=2)
bar  = ax3.bar(api_data.columns[2:], api_data.iloc[0, 2:])
ax3.set_ylim(0, 100)

legend = ax2.legend(api_data.iloc[:, 2:].columns, loc=2, bbox_to_anchor=(1.05, 1), borderaxespad=0.)

def do_calculation(i, filename):
    img = mpimg.imread('./video/in/' + filename)
    ax1.imshow(img)
    line.set_xdata([i, i])
    for j, b in enumerate(bar):
        b.set_height(api_data.iloc[i, 2+j])
    plt.savefig('./video/out/' + str(i) + '.png', bbox_extra_artists=(legend,), bbox_inches='tight')
    return i

if __name__ == '__main__':
    multiprocessing.log_to_stderr(logging.DEBUG)
    print(api_data.img_name.dtype)
    frames = api_data.img_name + '.png'

    pool_size = multiprocessing.cpu_count()
    with multiprocessing.Pool(processes = pool_size) as pool:
        pool.starmap(do_calculation, zip(np.arange(frames.shape[0]), list(frames)))
