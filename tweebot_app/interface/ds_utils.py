import pandas as pd
import plotly.graph_objects as go
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
chrome_options = Options()
chrome_options.add_argument('--headless')

class Summary:

    def __init__(self, filename):
        self.dat = pd.read_csv(filename)
        self.wc_dict = None

    def summary_stats(self, type, stat):
        stats = self.dat.describe().transpose().iloc[1:, :]
        try:
            return stats.loc[type][stat]
        except KeyError as e:
            raise KeyError('Possible columns include {}'.format(list(stats.columns)))

    def get_most_likes(self):
        row = self.dat[self.dat['likes']==self.dat['likes'].max()]
        tw_url = 'twitter.com/' + row['user_id'].values.flat[0] + '/status/' + str(row['tweet_id'].values.flat[0])
        return tw_url

    def get_most_re(self):
        row = self.dat[self.dat['retweets'] == self.dat['retweets'].max()]
        tw_url = 'twitter.com/' + row['user_id'].values.flat[0] + '/status/' + str(row['tweet_id'].values.flat[0])
        return tw_url

    def likes_retweets_plot(self):
        fig = go.Figure(data=[
                    go.Bar(name='Tweets', x=['Likes', 'Retweets'], y=[self.dat['likes'].sum(), self.dat['retweets'].sum()])
              ])
        fig.update_layout(
            title="Total Likes vs. Retweets",
            yaxis_title='Sum',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            width=400,
            height=400
        )
        return fig.to_html(include_plotlyjs='cdn')

    def wc(self, clean=True):
        col = 'clean_text'
        if not clean:
            col = 'text'

        wc = {}
        for tweet in self.dat[col]:
            for word in tweet.split():
                if word not in wc:
                    wc[word] = 1
                else:
                    wc[word] += 1

        wc = {k: v for k, v in sorted(wc.items(), key=lambda item: item[1], reverse=True)}
        self.wc_dict = wc

    def wc_plot(self, count=25):
        if not self.wc_dict:
            self.wc_dict()

        fig = go.Figure(data=[
            go.Bar(name='Word Count', x=list(self.wc_dict.keys())[:count], y=list(self.wc_dict.values())[:count])
        ])
        fig.update_xaxes(tickangle=45)
        fig.update_layout(
            title="Top {} Words".format(count),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            width=450,
            height=450
        )
        return fig.to_html(include_plotlyjs='cdn')


def embed_html(tweet_link):
    url = 'https://publish.twitter.com/?query=' + tweet_link.replace('/', '%2F') + '&theme=dark&widget=Tweet'

    browser = webdriver.Chrome(options=chrome_options)
    browser.get(url)
    html = browser.find_element_by_class_name('EmbedCode-code')

    return html.text

