from wumpy.models import Permissions, PermissionOverwrite, PermissionTarget


def test_permission_build() -> None:
    perms = Permissions.build(
        send_messages=True, embed_links=True, add_reactions=True, connect=True
    )

    assert perms.value == 1067072


def test_permission_replace() -> None:
    perms = Permissions.build(create_instant_invite=True, ban_members=True)
    assert perms.replace(kick_members=True, ban_members=False) == Permissions(3)


def test_overwrite_build() -> None:
    overwrite = PermissionOverwrite.build(
        344404945359077377, PermissionTarget.member,
        send_messages=True, send_messages_in_threads=True,
        mute_members=False, move_members=False, priority_speaker=False, stream=False
    )

    assert overwrite.allow == Permissions(274877908992)
    assert overwrite.deny == Permissions(20972288)


def test_overwrite_equality() -> None:
    a = PermissionOverwrite.build(
        344404945359077377, PermissionTarget.member,
        add_reactions=True, embed_links=False
    )
    b = PermissionOverwrite.build(
        344404945359077377, PermissionTarget.member,
        add_reactions=True, embed_links=False
    )
    assert a == b


def test_overwrite_different_id() -> None:
    a = PermissionOverwrite.build(
        344404945359077377, PermissionTarget.member,
        connect=True, speak=False
    )
    b = PermissionOverwrite.build(
        841509053422632990, PermissionTarget.member,
        connect=True, speak=False
    )
    assert not a == b
    assert a != b


def test_overwrite_inequality() -> None:
    a = PermissionOverwrite.build(
        344404945359077377, PermissionTarget.member,
        manage_roles=True, manage_nicknames=True, manage_channels=False
    )
    b = PermissionOverwrite.build(
        344404945359077377, PermissionTarget.member,
        manage_nicknames=True, manage_channels=True
    )
    assert a != b


def test_overwrite_replace() -> None:
    overwrite = PermissionOverwrite.build(
        344404945359077377, PermissionTarget.member,
        send_messages=True, send_messages_in_threads=True,
        add_reactions=False, embed_links=False
    )
    replaced = overwrite.replace(speak=True, send_messages_in_threads=False, embed_links=None)
    assert replaced.allow == Permissions(2099200)
    assert replaced.deny == Permissions(274877907008)
