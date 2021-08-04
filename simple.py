import threading
import requests
import os
import time
import json
import PySimpleGUI as sg

TIMEOUT = 5.0

class ListItem:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __str__(self):
        return f'{self.name}'


class PluginImpl:
    def __init__(self, player=None):
        self.player = player
        self.hot_data = []
        self.hot_data_thread = None
        self.stop_flag = False
        self.window = None
        self.loading_gif = sg.DEFAULT_BASE64_LOADING_GIF #os.path.join(os.path.dirname(__file__), "loading.gif")

    def show_loading(self, thread, msg):
        location = self.window.CurrentLocation()
        size = self.window.size
        while True:
            sg.popup_animated(self.loading_gif, msg, location=(location[0] + size[0] / 2 - 40, location[1] + size[1] / 2 - 40), time_between_frames=100)
            thread.join(timeout=.1)
            if not thread.is_alive():
                break
        sg.popup_animated(None)

    def show(self):
        treedata = sg.TreeData()
        tab_list = sg.Tab('list', [[sg.LBox(values=[],
                                            size=[60, 20],
                                            key='-LBOX-')]], key='-LIST-')

        tab_detail = sg.Tab('detail', [[sg.Tree(data=treedata,
                                                headings=[],
                                                auto_size_columns=False,
                                                key='-TREE-',
                                                visible_column_map =[False],
                                                show_expanded=True,
                                                text_color='#000000',
                                                background_color='#ffffff',
                                                enable_events=True)]], key='-DETAIL-')

        layout = [
            [sg.In('越狱', key='-Q-', ), sg.Btn('搜索', key='-SEARCH-'), sg.Btn('热门资源', key='-HOT-')],
            [sg.HSep()],
            [sg.TabGroup([[tab_list, tab_detail]], key="-TABG-")]
        ]
        self.window = window = sg.Window('人人影视', layout, size=(800, 600), resizable=True, finalize=True)

        window['-TABG-'].expand(True, True)
        window['-LBOX-'].expand(True, True)
        window['-TREE-'].expand(True, True)
        window['-TREE-'].Widget.configure(show='tree')
        window['-LBOX-'].bind('<Double-Button-1>', 'DBLCLICK')
        window['-TREE-'].bind('<Double-Button-1>', 'DBLCLICK')

        window.write_event_value('-HOT-', None)

        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED:
                break
            elif event == '-HOT-':
                thread = threading.Thread(target=self.get_hot_data, args=(window,), daemon=True)
                thread.start()
                self.show_loading(thread, 'Loading hot')
            elif event == '-SEARCH-':
                q = values['-Q-']
                if q:
                    thread = threading.Thread(target=self.search, args=(q, window,), daemon=True)
                    thread.start()
                    self.show_loading(thread, 'Loading search result')
            elif event == '-LBOX-DBLCLICK':
                thread = threading.Thread(target=self.get_detail, args=(values['-LBOX-'][0].id, window,), daemon=True)
                thread.start()
                self.show_loading(thread, 'Loading detail')
            elif event == '-HOT-RESULT-':
                window['-LBOX-'].update(values=values[event])
                window['-LIST-'].select()
            elif event == '-DETAIL-':
                treedata = sg.TreeData()
                name, result = values[event]
                for id, pid, text, value in result:
                    treedata.insert(pid, id, text, values=[value])
                window['-TREE-'].update(values=treedata)
                window['-DETAIL-'].update(title=f'{name} - detail')
                window['-DETAIL-'].select()
            elif event == '-SEARCH-RESULT-':
                window['-LBOX-'].update(values=values[event])
                window['-LIST-'].select()
            elif event == '-TREE-DBLCLICK':
                selected_row = window.Element('-TREE-').SelectedRows[0]
                values = window.Element('-TREE-').TreeData.tree_dict[selected_row].values
                if values and values[0] and self.player and self.player.play:
                    self.player.play(values[0])
            else:
                print(f'{event=}, {values=}')


        window.close()

    def get_hot_data(self, window):
        try:
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            top = requests.get("https://yyets.dmesg.app/api/top", headers=headers, timeout=TIMEOUT).json()
            result = [ListItem(i["data"]["info"]["id"], i["data"]["info"]["cnname"]) for i in top["ALL"]]
            window.write_event_value('-HOT-RESULT-', result)
        except:
            window.write_event_value('-HOT-RESULT-', [])

    def get_detail(self, id, window):
        name = ''
        result = []
        try:
            url = f"https://yyets.dmesg.app/api/resource?id={id}"
            referer = f'https://yyets.dmesg.app/resource?id={id}'
            detail = requests.get(url, headers={'referer': referer}, timeout=TIMEOUT).json()
            name = detail["data"]["info"]["cnname"]
            if "list" in detail["data"] and detail["data"]["list"]:
                for season in detail["data"]["list"]:
                    season_cn = season["season_cn"]
                    items = season["items"]
                    season_data = []
                    for collection_type in items:
                        collection = items[collection_type]
                        collection_data = []
                        for entry in collection:
                            entry_name = entry["name"]
                            if "files" in entry and entry["files"]:
                                for file in entry["files"]:
                                    if file["way"] == "2":
                                        collection_data.append((f'{season_cn}.{collection_type}.{entry_name}', f'{season_cn}.{collection_type}', entry_name, file["address"]))
                        if collection_data:
                            season_data.append((f'{season_cn}.{collection_type}', f'{season_cn}', collection_type, ''))
                            season_data += collection_data
                    if season_data:
                        result.append((f'{season_cn}', '', season_cn, ''))
                        result += season_data
            else:
                print("no resource")
        except:
            import traceback
            traceback.print_exc()
            pass
        window.write_event_value('-DETAIL-', (name, result))

    def search(self, q, window):
        try:
            params = {
                'keyword': q
            }
            url = 'https://yyets.dmesg.app/api/resource'
            results = requests.get(url, params=params, timeout=TIMEOUT).json()
            window.write_event_value('-SEARCH-RESULT-', [ListItem(i['data']['info']['id'], i['data']['info']['cnname']) for i in results['data']])
        except:
            print(json.dumps(results, indent=4))
            # return []
            import traceback
            traceback.print_exc()
            pass

def main():
    pi = PluginImpl()
    pi.show()

if __name__ == "__main__":
    main()
