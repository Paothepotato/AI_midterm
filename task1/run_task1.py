import sys
import os

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.board import Board
from core.constants import ACTIONS, STEP_COST


def demonstrate_state_space(map_path: str = 'maps/example_map.txt'):
    print('=' * 75)
    print(f'MINH HOA MO HINH HOA KHONG GIAN TRANG THAI: {map_path}')
    print('=' * 75)

    board = Board.from_file(map_path)
    print(f'\n[1] Thong tin ban do tinh (Board):')
    print(f' - Kich thuoc luoi : {board.width} x {board.height}')
    print(f' - So o tuong      : {len(board.walls)} o')
    print(f' - So o san di duoc: {len(board.floors)} o')
    print(f' - So o dich       : {len(board.goals)} o -> {sorted(list(board.goals))}')

    print(f'\n[2] Cac thanh phan cua bai toan tim kiem (State-Space Formulation):')
    print(f' - Trang thai ban dau (s0):')
    print(f'     Vi tri nguoi choi : {board.initial.player}')
    print(f'     Vi tri cac hop    : {board.initial.boxes}')
    print(f' - Tap hanh dong A(s)  : {list(ACTIONS.keys())}')
    print(f' - Chi phi buoc di c   : {STEP_COST}')
    print(f' - Dieu kien dich      : frozenset(state.boxes) == board.goals')
    print(f' - s0 da la dich chua? : {board.is_goal(board.initial)}')

    print(f'\n[3] Ban do truc quan ban dau:')
    print(board.render(board.initial))

    succs = board.successors(board.initial)
    print(f'\n[4] Cac trang thai ke tiep hop le tu s0 ({len(succs)} nuoc di):')
    for act, next_st in succs:
        print(f' - Hanh dong \'{act:5s}\' -> Nguoi choi: {next_st.player}, Hop: {next_st.boxes}')

    return board


def test_transitions_on_example_map():
    print('\n' + '=' * 75)
    print('KIEM CHUNG QUY TAC CHUYEN TRANG THAI TREN BAN DO MAU EXAMPLE_MAP')
    print('=' * 75)
    board = Board.from_file('maps/example_map.txt')
    s0 = board.initial
    print(f'Trang thai ban dau: {s0}')

    s_valid = board.move(s0, 'West')
    print(f'\nBuoc di hop le West -> {s_valid}')
    assert s_valid is not None and s_valid.player == (1, 2), 'Buoc di West phai hop le.'

    s_wall = board.move(s0, 'North')
    print(f'Buoc di dam tuong North -> {s_wall}')
    assert s_wall is None, 'Di vao tuong bat buoc phai tra ve None.'

    actions = [
        'East', 'North', 'East', 'East', 'South', 'South', 'South', 'South',
        'West', 'South', 'East', 'North', 'North', 'North', 'North', 'West',
        'West', 'West', 'East', 'South', 'East', 'South', 'East', 'South',
        'South', 'West', 'West', 'South', 'West', 'West', 'North', 'North',
        'South', 'East'
    ]
    print(f'\nPhat lai chuoi loi giai mau ({len(actions)} buoc):')
    history = board.replay(actions)
    print(f' - So buoc chuyen doi: {len(history) - 1}')
    print(f' - Trang thai cuoi   : Nguoi={history[-1].player}, Hop={history[-1].boxes}')
    assert board.is_goal(history[-1]), 'Trang thai cuoi cung bat buoc phai dat muc tieu (Goal State)!'
    print('-> Luat chuyen trang thai va tinh nang replay kiem chung THANH CONG!\n')


if __name__ == '__main__':
    demonstrate_state_space('maps/example_map.txt')
    test_transitions_on_example_map()
    print('Tat ca cac thanh phan cua Task 1 da vuot qua kiem thu thanh cong tren example_map!')
